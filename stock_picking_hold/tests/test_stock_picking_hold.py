from datetime import datetime

from dateutil import relativedelta

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
        stock_location = self.env.ref("stock.stock_location_stock")
        customer_location = self.env.ref("stock.stock_location_customers")
        picking_type_out = self.env.ref("stock.picking_type_out")

        stock_picking_id = self.env["stock.picking"].create(
            {
                "partner_id": self.partner_id.id,
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
                "picking_type_id": picking_type_out.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": "test_out_1",
                            "location_id": stock_location.id,
                            "location_dest_id": customer_location.id,
                            "product_id": self.product1.id,
                            "product_uom": self.product1.uom_id.id,
                            "product_uom_qty": 1.0,
                            "picking_type_id": picking_type_out.id,
                            "date": datetime.today()
                            + relativedelta.relativedelta(days=7.0),
                        },
                    )
                ],
            }
        )

        stock_picking_id.action_confirm()

        self.assertEqual(stock_picking_id.hold, False)

        stock_picking_id.action_hold()

        self.assertEqual(stock_picking_id.hold, True)

        with self.assertRaises(UserError):
            stock_picking_id.button_validate()

        stock_picking_id.action_unhold()

        self.assertNotEqual(stock_picking_id.hold, True)
