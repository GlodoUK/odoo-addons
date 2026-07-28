from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.delivery.tests.common import DeliveryCommon
from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestCheckProductPricelistDelivery(DeliveryCommon, SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.priced_product = cls._create_product(name="Priced Product")
        cls.pricelist.write(
            {
                "check_sale_behaviour": "explicit",
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "1_product",
                            "product_tmpl_id": cls.priced_product.product_tmpl_id.id,
                            "compute_price": "fixed",
                            "fixed_price": 10.0,
                        }
                    ),
                ],
            }
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "pricelist_id": cls.pricelist.id,
                "order_line": [Command.create({"product_id": cls.priced_product.id})],
            }
        )
        cls.order.set_delivery_line(cls.carrier, cls.carrier.fixed_price)
        cls.delivery_line = cls.order.order_line.filtered("is_delivery")

    def test_delivery_line_is_exempt(self):
        """The carrier product is not on the pricelist, but ships anyway."""
        self.assertTrue(self.delivery_line)
        self.assertFalse(self.delivery_line.pricelist_item_id)

        self.assertTrue(self.delivery_line._pricelist_check_sale_behaviour())
        self.assertFalse(self.order._confirmation_error_message())

        self.order.action_confirm()
        self.assertEqual(self.order.state, "sale")

    def test_exemption_does_not_leak_to_other_lines(self):
        """Only is_delivery lines are exempt; the rest are still checked."""
        unpriced_line = self.env["sale.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": self._create_product(name="Unpriced Product").id,
            }
        )

        self.assertFalse(unpriced_line.is_delivery)
        self.assertFalse(unpriced_line._pricelist_check_sale_behaviour())
        self.assertTrue(self.order._confirmation_error_message())
