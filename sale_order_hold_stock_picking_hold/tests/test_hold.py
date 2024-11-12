from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestStockPickingHold(TransactionCase):
    def setUp(self):
        super(TestStockPickingHold, self).setUp()

        self.partner_id = self.env["res.partner"].create(
            {"name": "Test Customer", "customer_rank": 1}
        )
        prod_categ_all_id = self.env.ref("product.product_category_all")

        self.product1 = self.env["product.product"].create(
            {"name": "Product A", "type": "product", "categ_id": prod_categ_all_id.id}
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
                            "product_id": self.product1.id,
                            "product_uom_qty": 1.0,
                        },
                    )
                ],
            }
        )

        sale_id.action_confirm()

        stock_picking_id = sale_id.picking_ids

        self.assertEqual(stock_picking_id.hold, False)

        sale_id.action_hold()

        self.assertEqual(stock_picking_id.hold, True)

        with self.assertRaises(UserError):
            stock_picking_id.button_validate()

        with self.assertRaises(UserError):
            stock_picking_id.action_unhold()

        sale_id.action_unhold()

        self.assertNotEqual(stock_picking_id.hold, True)
