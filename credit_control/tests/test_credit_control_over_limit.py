from odoo.exceptions import UserError
from odoo.tests import tagged

from .credit_test_classes import CreditControlTestCase


@tagged("post_install", "-at_install")
class TestCreditControlOverLimit(CreditControlTestCase):
    def test_over_limit_policy(self):
        credit_control_policy_id = self.env["credit.control.policy"].create(
            {
                "name": "Overlimit Test Policy",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Over limit",
                            "rule": "over_limit",
                            "classification_id": self.classification_accounts.id,
                        },
                    )
                ],
            }
        )

        self.partner_id.write(
            {
                "credit_control_policy_id": credit_control_policy_id.id,
                "credit_control_limit": 5,
            }
        )

        self.assertEqual(self.partner_id.credit_control_used, 0)

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
                            "product_uom_qty": 2,
                            "product_uom": self.product2.uom_id.id,
                            "price_unit": 100,
                            "tax_id": False,
                        },
                    )
                ],
            }
        )

        with self.assertRaises(
            UserError, msg="SO should not confirm when credit_limit is exceeded"
        ):
            sale_order_id.action_confirm()

    def test_under_limit_policy(self):
        credit_control_policy_id = self.env["credit.control.policy"].create(
            {
                "name": "Overlimit Test Policy",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Over limit",
                            "rule": "over_limit",
                            "classification_id": self.classification_accounts.id,
                        },
                    )
                ],
            }
        )

        self.partner_id.write(
            {
                "credit_control_policy_id": credit_control_policy_id.id,
                "credit_control_limit": 300,
            }
        )

        self.assertEqual(self.partner_id.credit_control_used, 0)

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
        self.partner_id._compute_credit_control_used()

        self.assertEqual(self.partner_id.credit_control_used, 194.96)
