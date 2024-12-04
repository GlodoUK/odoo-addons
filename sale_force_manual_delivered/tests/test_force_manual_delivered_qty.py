from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestForceManualDeliveredQty(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_id = self.env["res.partner"].create({"name": "Test Partner"})

        self.product_id = self.env["product.product"].create({"name": "Product A"})

    def test_force_manual_delivered_qty(self):
        sale_order_id = self.env["sale.order"].create(
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
        sale_order_id.order_line[0].force_manual_delivered_qty = True

        self.assertEqual(sale_order_id.order_line[0].qty_delivered_method, "manual")
