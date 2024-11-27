from odoo.tests import tagged

from odoo.addons.component.core import Component
from odoo.addons.component.tests.common import ComponentRegistryCase
from odoo.addons.stock.tests.common import TestStockCommon


@tagged("post_install", "-at_install")
class TestPickingIn(ComponentRegistryCase, TestStockCommon):
    def setUp(cls):  # noqa: B902
        super().setUp()
        ComponentRegistryCase._setup_registry(cls)

        cls.picking_assigned = []

        cls.picking_in_done = []
        cls.picking_out_done = []

        cls.picking_out_cancel = []
        cls.picking_in_cancel = []

        class StockPickingListener(Component):
            _name = "test.stock.picking.listener"
            _inherit = "base.event.listener"
            _apply_on = ["stock.picking"]

            def on_picking_assigned(self, picking):
                cls.picking_assigned.append(picking.id)

            def on_picking_out_done(self, picking, method):
                cls.picking_out_done.append(picking.id)

            def on_picking_out_dropship_done(self, picking, method):
                raise NotImplementedError()

            def on_picking_in_done(self, picking, method):
                cls.picking_in_done.append(picking.id)

            def on_picking_out_cancel(self, picking):
                cls.picking_out_cancel.append(picking.id)

            def on_picking_out_dropship_cancel(self, picking):
                raise NotImplementedError()

            def on_picking_in_cancel(self, picking):
                cls.picking_in_cancel.append(picking.id)

        StockPickingListener._build_component(cls.comp_registry)

    def test_picking_out_cancel(self):
        """
        Test the events when an outbound picking is cancelled.
        """
        picking_out = self.PickingObj.create(
            {
                "picking_type_id": self.picking_type_out,
                "location_id": self.stock_location,
                "location_dest_id": self.customer_location,
            }
        )

        self.MoveObj.create(
            {
                "name": self.productA.name,
                "product_id": self.productA.id,
                "product_uom_qty": 1,
                "product_uom": self.productA.uom_id.id,
                "picking_id": picking_out.id,
                "location_id": self.stock_location,
                "location_dest_id": self.customer_location,
            }
        )

        picking_out.action_confirm()
        picking_out.action_assign()
        self.assertListEqual(
            self.picking_assigned, [], "picking should not yet have any stock assigned!"
        )

        picking_out.action_cancel()
        self.assertListEqual(
            self.picking_out_cancel,
            [picking_out.id],
            "picking should have been cancelled!",
        )
        self.assertListEqual(self.picking_in_cancel, [])

    def test_picking_in_cancel(self):
        """
        Test the events when an inbound picking is cancelled.
        """
        picking_in = self.PickingObj.create(
            {
                "picking_type_id": self.picking_type_in,
                "location_id": self.supplier_location,
                "location_dest_id": self.stock_location,
            }
        )

        self.MoveObj.create(
            {
                "name": self.productA.name,
                "product_id": self.productA.id,
                "product_uom_qty": 1,
                "product_uom": self.productA.uom_id.id,
                "picking_id": picking_in.id,
                "location_id": self.supplier_location,
                "location_dest_id": self.stock_location,
            }
        )

        picking_in.action_confirm()
        picking_in.action_assign()
        self.assertListEqual(self.picking_assigned, [picking_in.id])

        picking_in.action_cancel()
        self.assertListEqual(
            self.picking_in_cancel,
            [picking_in.id],
            "picking should have been cancelled!",
        )
        self.assertListEqual(self.picking_out_cancel, [])

    def test_picking_workflow(self):
        """Test the events in a standard supplier -> stock -> customer workflow."""
        picking_out = self.PickingObj.create(
            {
                "picking_type_id": self.picking_type_out,
                "location_id": self.stock_location,
                "location_dest_id": self.customer_location,
            }
        )

        move_out_a = self.MoveObj.create(
            {
                "name": self.productA.name,
                "product_id": self.productA.id,
                "product_uom_qty": 1,
                "product_uom": self.productA.uom_id.id,
                "picking_id": picking_out.id,
                "location_id": self.stock_location,
                "location_dest_id": self.customer_location,
            }
        )

        picking_out.action_confirm()
        picking_out.action_assign()

        self.assertListEqual(
            self.picking_assigned, [], "picking should not yet have any stock assigned!"
        )

        picking_in = self.PickingObj.create(
            {
                "picking_type_id": self.picking_type_in,
                "location_id": self.supplier_location,
                "location_dest_id": self.stock_location,
            }
        )

        move_in_a = self.MoveObj.create(
            {
                "name": self.productA.name,
                "product_id": self.productA.id,
                "product_uom_qty": 1,
                "product_uom": self.productA.uom_id.id,
                "picking_id": picking_in.id,
                "location_id": self.supplier_location,
                "location_dest_id": self.stock_location,
            }
        )

        picking_in.action_confirm()
        picking_in.action_assign()

        self.assertListEqual(self.picking_assigned, [picking_in.id])

        move_in_a.move_line_ids.qty_done = 1
        picking_in._action_done()

        self.assertListEqual(self.picking_in_done, [picking_in.id])

        picking_out.action_assign()

        self.assertListEqual(self.picking_assigned, [picking_in.id, picking_out.id])

        move_out_a.move_line_ids.qty_done = 1
        picking_out._action_done()

        self.assertListEqual(self.picking_out_done, [picking_out.id])
