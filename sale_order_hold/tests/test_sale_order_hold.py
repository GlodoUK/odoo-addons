from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleOrderHold(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_id = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        cls.product_id = cls.env["product.product"].create({"name": "Test Product"})

    def test_sale_order_hold(self):
        order_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
            }
        )

        self.env["sale.order.line"].create(
            {
                "order_id": order_id.id,
                "product_id": self.product_id.id,
                "product_uom_qty": 1.0,
            }
        )

        self.assertFalse(order_id.hold, "The order should not be on hold!")

        reason_ids = self.env.ref("sale_order_hold.sale_order_hold_reason_wrong_item")

        order_id.action_hold(reason_id=reason_ids)

        self.assertTrue(order_id.hold, "The order should be on hold!")

        self.assertEqual(
            order_id.hold_reason_ids,
            reason_ids,
            f"The hold reason should be {reason_ids.name}!",
        )

        order_id.action_unhold()

        self.assertFalse(order_id.hold, "The order should not be on hold!")

        self.assertFalse(
            order_id.hold_reason_ids, "The order should not have hold reasons!"
        )
