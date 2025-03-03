from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestForceDeliveryLine(TransactionCase):
    def setUp(self):
        super().setUp()

        self.SaleOrder = self.env["sale.order"]
        self.SaleOrderLine = self.env["sale.order.line"]

        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.product_delivery_normal = self.env["product.product"].create(
            {
                "name": "Normal Delivery Charges",
                "type": "service",
                "list_price": 10.0,
                "categ_id": self.env.ref("delivery.product_category_deliveries").id,
            }
        )

    def test_force_delivery_cost(self):
        sale_order = self.env["sale.order"].create({"partner_id": self.partner.id})

        self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product_delivery_normal.id,
                "is_delivery": False,
            }
        )

        with self.assertRaises(UserError):
            sale_order.action_confirm()

        self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product_delivery_normal.id,
                "is_delivery": True,
            }
        )

        sale_order.action_confirm()

        self.assertEqual(sale_order.state, "sale")
