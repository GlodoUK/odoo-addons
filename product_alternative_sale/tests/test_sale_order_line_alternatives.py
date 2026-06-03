from odoo import Command
from odoo.tests.common import TransactionCase


class TestSaleOrderLineAlternatives(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Template = cls.env["product.template"]
        cls.target = Template.create({"name": "Alt Target", "list_price": 50.0})
        cls.source = Template.create({"name": "Alt Source", "list_price": 100.0})
        cls.no_alt = Template.create({"name": "No Alternatives"})
        cls.env["product.alternative"].create(
            {
                "product_tmpl_id": cls.source.id,
                "alternative_tmpl_id": cls.target.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})

    def _line(self, product):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [Command.create({"product_id": product.id})],
            }
        )
        return order.order_line

    def test_widget_shows_alternatives(self):
        line = self._line(self.source.product_variant_id)
        self.assertTrue(line.display_alternatives_widget)

    def test_widget_hidden_without_alternatives(self):
        line = self._line(self.no_alt.product_variant_id)
        self.assertFalse(line.display_alternatives_widget)

    def test_catalog_action_restricted_to_alternatives(self):
        line = self._line(self.source.product_variant_id)
        action = line.action_view_alternatives_catalog()
        self.assertEqual(action["res_model"], "product.product")
        matched = self.env["product.product"].search(action["domain"])
        self.assertIn(self.target.product_variant_id, matched)
        self.assertNotIn(self.source.product_variant_id, matched)
        self.assertNotIn(self.no_alt.product_variant_id, matched)
