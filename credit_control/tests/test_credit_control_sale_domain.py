from odoo.exceptions import UserError
from odoo.tests import tagged

from .credit_test_classes import CreditControlTestCase


@tagged("post_install", "-at_install")
class TestCreditControlSaleDomain(CreditControlTestCase):
    def test_sale_policy_matches(self):
        credit_control_policy_id = self.env["credit.control.policy"].create(
            {
                "name": "Sale Domain Test Policy",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "sale_domain",
                            "rule": "sale_domain",
                            "sale_domain": [("partner_id.id", "=", self.partner_id.id)],
                            "classification_id": self.classification_sales.id,
                        },
                    ),
                ],
            }
        )

        self.partner_id.write({"credit_control_policy_id": credit_control_policy_id.id})

        sale_order_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "partner_invoice_id": self.partner_id.id,
                "partner_shipping_id": self.partner_id.id,
                "pricelist_id": self.pricelist_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product2.name,
                            "product_id": self.product2.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product2.uom_id.id,
                            "price_unit": 100,
                            "tax_id": False,
                        },
                    )
                ],
            }
        )

        with self.assertRaises(UserError):
            sale_order_id.action_confirm()

    def test_sale_policy_not_matches(self):
        credit_control_policy_id = self.env["credit.control.policy"].create(
            {
                "name": "Sale Domain Test Policy",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "sale_domain",
                            "rule": "sale_domain",
                            "sale_domain": [
                                ("partner_id.id", "!=", self.partner_id.id)
                            ],
                            "classification_id": self.classification_sales.id,
                        },
                    ),
                ],
            }
        )

        self.partner_id.write({"credit_control_policy_id": credit_control_policy_id.id})

        sale_order_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "partner_invoice_id": self.partner_id.id,
                "partner_shipping_id": self.partner_id.id,
                "pricelist_id": self.pricelist_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product2.name,
                            "product_id": self.product2.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product2.uom_id.id,
                            "price_unit": 100,
                            "tax_id": False,
                        },
                    )
                ],
            }
        )

        sale_order_id.action_confirm()
