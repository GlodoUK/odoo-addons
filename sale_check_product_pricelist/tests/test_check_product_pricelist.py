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

    def _create_order(self, product, pricelist=None):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": (pricelist or self.pricelist).id,
                "order_line": [Command.create({"product_id": product.id})],
            }
        )

    def _line(self, order, product):
        """The order's line for `product`.

        Other modules add lines of their own - sale_delivery_auto puts a
        shipping cost line on anything physical - so never read `order_line` as
        a single record.
        """
        return order.order_line.filtered(lambda line: line.product_id == product)

    def test_default_behaviour_ignores_pricelist(self):
        """The Odoo default sells anything, priced on the pricelist or not."""
        self.assertEqual(self.pricelist.check_sale_behaviour, "default")
        order = self._create_order(self.unpriced_product)
        line = self._line(order, self.unpriced_product)

        # 'default' is permissive precisely because nothing implements it: the
        # dispatch reads a missing hook as "no check".
        self.assertFalse(hasattr(line, "_pricelist_check_sale_behaviour_default"))
        self.assertFalse(line.pricelist_item_id)
        self.assertTrue(line._pricelist_check_sale_behaviour())
        self.assertFalse(order._confirmation_error_message())

        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_explicit_behaviour_blocks_unpriced_product(self):
        """Under 'explicit', a product with no matching rule blocks confirmation."""
        self.pricelist.check_sale_behaviour = "explicit"
        order = self._create_order(self.unpriced_product)
        line = self._line(order, self.unpriced_product)

        self.assertFalse(line._pricelist_check_sale_behaviour())
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
        line = self._line(order, self.priced_product)

        self.assertTrue(line.pricelist_item_id)
        self.assertTrue(line._pricelist_check_sale_behaviour())
        self.assertFalse(order._confirmation_error_message())

        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def _child_pricelist(self, behaviour="explicit"):
        """An explicit pricelist whose only rule passes everything on to
        `self.pricelist`, the way a customer pricelist falls back to its
        parent."""
        return self.env["product.pricelist"].create(
            {
                "name": "Child Pricelist",
                "check_sale_behaviour": behaviour,
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "pricelist",
                            "base_pricelist_id": self.pricelist.id,
                        }
                    ),
                ],
            }
        )

    def test_explicit_descends_to_parent_priced(self):
        """A catch-all onto an explicit parent passes a product the parent
        prices."""
        self.pricelist.check_sale_behaviour = "explicit"
        child = self._child_pricelist()
        order = self._create_order(pricelist=child, product=self.priced_product)
        line = self._line(order, self.priced_product)

        self.assertEqual(line.pricelist_item_id.pricelist_id, child)
        self.assertTrue(line._pricelist_check_sale_behaviour())
        self.assertFalse(order._confirmation_error_message())

    def test_explicit_descends_to_parent_unpriced(self):
        """A catch-all onto an explicit parent does not make a product the
        parent does not price sellable."""
        self.pricelist.check_sale_behaviour = "explicit"
        child = self._child_pricelist()
        order = self._create_order(pricelist=child, product=self.unpriced_product)
        line = self._line(order, self.unpriced_product)

        # The child's catch-all matches; it is the parent that has no rule
        self.assertTrue(line.pricelist_item_id)
        self.assertFalse(line._pricelist_check_sale_behaviour())
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_explicit_stops_at_permissive_parent(self):
        """A parent on the Odoo default sells anything, so the chain stops
        there."""
        self.assertEqual(self.pricelist.check_sale_behaviour, "default")
        child = self._child_pricelist()
        order = self._create_order(pricelist=child, product=self.unpriced_product)
        line = self._line(order, self.unpriced_product)

        self.assertTrue(line._pricelist_check_sale_behaviour())

    def test_skip_context(self):
        """skip_sale_check_product_pricelist in the context skips the check."""
        self.pricelist.check_sale_behaviour = "explicit"
        order = self._create_order(self.unpriced_product)
        line = self._line(order, self.unpriced_product)

        self.assertFalse(line._pricelist_check_sale_behaviour())
        self.assertTrue(
            line.with_context(
                skip_sale_check_product_pricelist=True
            )._pricelist_check_sale_behaviour()
        )
