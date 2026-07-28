from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestCheckProductPricelist(SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.priced_product = cls._create_product(name="Priced Product")
        cls.unpriced_product = cls._create_product(name="Unpriced Product")
        cls.pricelist.item_ids = [
            Command.create(
                {
                    "applied_on": "1_product",
                    "product_tmpl_id": cls.priced_product.product_tmpl_id.id,
                    "compute_price": "fixed",
                    "fixed_price": 10.0,
                }
            ),
        ]

    def _create_order(self, product):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "order_line": [Command.create({"product_id": product.id})],
            }
        )

    def test_default_behaviour_ignores_pricelist(self):
        """The Odoo default sells anything, priced on the pricelist or not."""
        self.assertEqual(self.pricelist.check_sale_behaviour, "default")
        order = self._create_order(self.unpriced_product)

        # 'default' is permissive precisely because nothing implements it: the
        # dispatch reads a missing hook as "no check".
        self.assertFalse(
            hasattr(order.order_line, "_pricelist_check_sale_behaviour_default")
        )
        self.assertFalse(order.order_line.pricelist_item_id)
        self.assertTrue(order.order_line._pricelist_check_sale_behaviour())
        self.assertFalse(order._confirmation_error_message())

        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_explicit_behaviour_blocks_unpriced_product(self):
        """Under 'explicit', a product with no matching rule blocks confirmation."""
        self.pricelist.check_sale_behaviour = "explicit"
        order = self._create_order(self.unpriced_product)

        self.assertFalse(order.order_line._pricelist_check_sale_behaviour())
        self.assertIn(
            self.unpriced_product.display_name,
            order._confirmation_error_message(),
        )
        with self.assertRaises(UserError):
            order.action_confirm()
        self.assertEqual(order.state, "draft")

    def test_explicit_behaviour_allows_priced_product(self):
        """Under 'explicit', a product matched by a rule confirms as normal."""
        self.pricelist.check_sale_behaviour = "explicit"
        order = self._create_order(self.priced_product)

        self.assertTrue(order.order_line.pricelist_item_id)
        self.assertTrue(order.order_line._pricelist_check_sale_behaviour())
        self.assertFalse(order._confirmation_error_message())

        order.action_confirm()
        self.assertEqual(order.state, "sale")
