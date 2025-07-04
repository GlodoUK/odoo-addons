from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestForceManualDeliveredQty(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partnerA = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        cls.productA = cls.env["product.product"].create(
            {
                "name": "Product A",
                "is_storable": True,
            }
        )

    def test_force_manual_delivered_qty(self):
        order_id = self.env["sale.order"].create(
            {
                "partner_id": self.partnerA.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.productA.id,
                            "product_uom_qty": 1.0,
                        },
                    )
                ],
            }
        )

        self.assertEqual(
            order_id.order_line.qty_delivered_method,
            "stock_move",
        )

        order_id.order_line.force_manual_delivered_qty = True

        self.assertEqual(
            order_id.order_line.qty_delivered_method,
            "manual",
        )
