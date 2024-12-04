from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestHold(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_id = self.env["res.partner"].create(
            {"name": "Test Customer", "customer_rank": 1}
        )

        self.product1 = self.env["product.product"].create({"name": "Product A"})

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

        self.assertFalse(sale_id.hold)

        reason_ids = self.env.ref("sale_order_hold.sale_order_hold_reason_wrong_item")

        sale_id.action_hold(reason_id=reason_ids)

        self.assertTrue(sale_id.hold)
        self.assertEqual(sale_id.hold_reason_ids, reason_ids)

        sale_id.action_unhold()

        self.assertFalse(sale_id.hold)
        self.assertFalse(sale_id.hold_reason_ids)
