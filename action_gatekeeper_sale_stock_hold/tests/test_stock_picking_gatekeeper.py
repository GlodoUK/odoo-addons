from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStockPickingGatekeeper(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create({"name": "Gatekeeper Partner"})

        cls.rule = cls.env["gatekeeper.rule"].create(
            {
                "name": "Sale Confirm Hold",
                "target_model": "sale.order",
                "trigger": "action_confirm",
                "rule": "always",
                "action": "hold",
            }
        )

    def _make_order_with_picking(self):
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        picking = self.env["stock.picking"].create(
            {
                "sale_id": order.id,
                "partner_id": self.partner.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )
        return order, picking

    def test_action_confirm_holds_pickings(self):
        order, picking = self._make_order_with_picking()
        order.action_confirm()
        self.assertTrue(order.gatekeeper_hold)
        self.assertTrue(picking.gatekeeper_hold)
        self.assertTrue(picking.hold)

    def test_releasing_hold_releases_pickings(self):
        order, picking = self._make_order_with_picking()
        order.action_confirm()
        order.gatekeeper_rule_lines.action_release()
        self.assertFalse(order.gatekeeper_hold)
        self.assertFalse(picking.gatekeeper_hold)
        self.assertFalse(picking.hold)

    def test_action_unhold_blocked_while_gatekeeper_hold(self):
        _, picking = self._make_order_with_picking()
        picking.gatekeeper_hold = True
        with self.assertRaises(UserError):
            picking.action_unhold()

    def test_action_cancel_clears_gatekeeper_hold(self):
        _, picking = self._make_order_with_picking()
        picking.gatekeeper_hold = True
        picking.action_cancel()
        self.assertFalse(picking.gatekeeper_hold)
