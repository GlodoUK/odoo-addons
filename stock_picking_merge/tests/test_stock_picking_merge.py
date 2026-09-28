from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.stock.tests.common import TestStockCommon


@tagged("post_install", "-at_install")
class TestStockPickingMerge(TestStockCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_type_in.allow_merge = True

    def _make_picking(
        self, picking_type=None, location=None, location_dest=None, confirm=False
    ):
        picking_type = picking_type or self.picking_type_in
        location = location or self.supplier_location
        location_dest = location_dest or self.stock_location
        picking = self.PickingObj.create(
            {
                "picking_type_id": picking_type.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
            }
        )
        self.MoveObj.create(
            {
                "product_id": self.productA.id,
                "product_uom_qty": 1,
                "product_uom": self.productA.uom_id.id,
                "picking_id": picking.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
            }
        )
        if confirm:
            picking.action_confirm()
        return picking

    def test_merge_three_pickings(self):
        p1 = self._make_picking()
        p2 = self._make_picking()
        p3 = self._make_picking()

        target = (p1 | p2 | p3)._action_merge()

        self.assertEqual(target, p1)
        self.assertEqual(len(target.move_ids), 3)
        self.assertEqual(p2.state, "cancel")
        self.assertEqual(p3.state, "cancel")

    def test_merge_three_pickings_manual_target(self):
        p1 = self._make_picking()
        p2 = self._make_picking()
        p3 = self._make_picking()

        target = (p1 | p2 | p3)._action_merge(p3)

        self.assertEqual(target, p3)
        self.assertEqual(len(target.move_ids), 3)
        self.assertEqual(p1.state, "cancel")
        self.assertEqual(p2.state, "cancel")

    def test_merge_confirmed_pickings(self):
        p1 = self._make_picking(confirm=True)
        p2 = self._make_picking(confirm=True)

        target = (p1 | p2)._action_merge()

        self.assertEqual(target, p1)
        self.assertEqual(len(target.move_ids), 2)
        self.assertEqual(p2.state, "cancel")

    def test_merge_requires_at_least_two(self):
        p1 = self._make_picking()
        with self.assertRaises(UserError):
            p1._action_merge()

    def test_merge_blocked_when_allow_merge_false(self):
        self.picking_type_in.allow_merge = False
        p1 = self._make_picking()
        p2 = self._make_picking()
        with self.assertRaises(UserError):
            (p1 | p2)._action_merge()
        self.picking_type_in.allow_merge = True

    def test_merge_blocked_for_done_state(self):
        p1 = self._make_picking()
        p2 = self._make_picking()
        # Simulate a done picking by directly setting state on the move
        p2.move_ids.write({"state": "done"})
        with self.assertRaises(UserError):
            (p1 | p2)._action_merge()

    def test_merge_blocked_for_cancel_state(self):
        p1 = self._make_picking()
        p2 = self._make_picking()
        p2.action_cancel()
        with self.assertRaises(UserError):
            (p1 | p2)._action_merge()

    def test_merge_blocked_for_different_picking_types(self):
        p1 = self._make_picking(picking_type=self.picking_type_in)
        self.picking_type_out.allow_merge = True
        p2 = self._make_picking(
            picking_type=self.picking_type_out,
            location=self.stock_location,
            location_dest=self.customer_location,
        )
        with self.assertRaises(UserError):
            (p1 | p2)._action_merge()

    def test_merge_blocked_for_different_source_locations(self):
        p1 = self._make_picking()
        p2 = self.PickingObj.create(
            {
                "picking_type_id": self.picking_type_in.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )
        self.MoveObj.create(
            {
                "product_id": self.productA.id,
                "product_uom_qty": 1,
                "product_uom": self.productA.uom_id.id,
                "picking_id": p2.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )
        with self.assertRaises(UserError):
            (p1 | p2)._action_merge()

    def test_merge_blocked_for_different_dest_locations(self):
        p1 = self._make_picking()
        p2 = self.PickingObj.create(
            {
                "picking_type_id": self.picking_type_in.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.shelf_1.id,
            }
        )
        self.MoveObj.create(
            {
                "product_id": self.productA.id,
                "product_uom_qty": 1,
                "product_uom": self.productA.uom_id.id,
                "picking_id": p2.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.shelf_1.id,
            }
        )
        with self.assertRaises(UserError):
            (p1 | p2)._action_merge()

    def test_merge_preserves_all_moves(self):
        p1 = self._make_picking()
        p2 = self._make_picking()
        # Add a second move to p2
        self.MoveObj.create(
            {
                "product_id": self.productC.id,
                "product_uom_qty": 5,
                "product_uom": self.productC.uom_id.id,
                "picking_id": p2.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )
        products_before = set((p1 | p2).move_ids.mapped("product_id.id"))

        target = (p1 | p2)._action_merge()

        products_after = set(target.move_ids.mapped("product_id.id"))
        self.assertEqual(
            products_before, products_after, "No moves should be lost during merge"
        )

    def test_wizard_creates_and_returns_action(self):
        p1 = self._make_picking()
        p2 = self._make_picking()
        from odoo.fields import Command

        wizard = self.env["stock.picking.merge.wizard"].create(
            {
                "picking_ids": [Command.set((p1 | p2).ids)],
            }
        )
        self.assertEqual(wizard.target_picking_id, p1)
        action = wizard.action_merge()
        self.assertEqual(action["res_model"], "stock.picking")
        self.assertEqual(action["res_id"], p1.id)
        self.assertEqual(p2.state, "cancel")
