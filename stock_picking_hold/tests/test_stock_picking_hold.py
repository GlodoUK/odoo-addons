from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestStockPickingHold(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_id = self.env["res.partner"].create(
            {
                "name": "Test Customer",
            }
        )

        self.product_id = self.env["product.product"].create(
            {
                "name": "Test Product",
            }
        )

        self.picking_id = self.env["stock.picking"].create(
            {
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "partner_id": self.partner_id.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )

        self.move_id = self.env["stock.move"].create(
            {
                "name": "Test Out 1",
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "product_id": self.product_id.id,
                "product_uom": self.product_id.uom_id.id,
                "product_uom_qty": 1.0,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "date": fields.Date.today() + relativedelta(days=7),
            }
        )

    def test_stock_picking_hold_01(self):
        """
        Call action_confirm()       Confirm picking is not held
        Call action_hold()          Confirm picking is held
        Call button_validate()      Confirm that UserError is raised
        Call action_unhold()        Confirm picking is not held
        """

        self.picking_id.action_confirm()

        self.assertFalse(
            self.picking_id.hold, "The stock picking should not be on hold!"
        )

        self.picking_id.action_hold()

        self.assertTrue(
            self.picking_id.hold,
            "The stock picking should be on hold!",
        )

        with self.assertRaises(UserError):
            self.picking_id.button_validate()

        self.picking_id.action_unhold()

        self.assertFalse(
            self.picking_id.hold, "The stock picking should not be on hold!"
        )

    def test_stock_picking_hold_02(self):
        """
        Call action_confirm()       Confirm picking is not held
        Call action_hold()          Confirm picking is held
        Call action_cancel()        Confirm that picking is not held
        """

        self.picking_id.action_confirm()

        self.assertFalse(
            self.picking_id.hold, "The stock picking should not be on hold!"
        )

        self.picking_id.action_hold()

        self.assertTrue(self.picking_id.hold, "The stock picking should be on hold!")

        self.picking_id.action_cancel()

        self.assertFalse(
            self.picking_id.hold,
            "The stock picking should not be on hold!",
        )

        self.assertEqual(
            self.picking_id.state,
            "cancel",
            "The stock picking should be cancelled!",
        )
