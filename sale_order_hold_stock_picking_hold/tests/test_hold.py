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
                "name": "Product A",
            }
        )

    def test_hold_unhold(self):
        sale_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.id,
                            "product_uom_qty": 1.0,
                        },
                    )
                ],
            }
        )

        sale_id.action_confirm()

        self.assertTrue(
            sale_id.picking_ids, "The sales order should have a linked picking!"
        )

        self.assertFalse(
            sale_id.picking_ids.hold, "The linked picking should not be on hold!"
        )

        sale_id.action_hold()

        self.assertTrue(sale_id.picking_ids, "The linked picking should be on hold!")

        with self.assertRaises(UserError):
            sale_id.picking_ids.button_validate()

        with self.assertRaises(UserError):
            sale_id.picking_ids.action_unhold()

        sale_id.action_unhold()

        self.assertFalse(
            sale_id.picking_ids.hold, "The linked picking should not be on hold!"
        )

    def test_hold_before_confirm(self):
        order = self.env["sale.order"].create({"partner_id": self.partner_id.id})
        self.env["sale.order.line"].create(
            {"product_id": self.product_id.id, "order_id": order.id}
        )

        order.action_hold()
        order.action_confirm()

        self.assertEqual(len(order.picking_ids), 1)
        self.assertTrue(False not in order.picking_ids.mapped("hold"))
