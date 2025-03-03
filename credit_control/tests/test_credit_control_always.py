from odoo.exceptions import UserError
from odoo.tests import tagged

from .credit_test_classes import CreditControlTestCase


@tagged("post_install", "-at_install")
class TestCreditControlAlways(CreditControlTestCase):
    def test_always_policy(self):
        credit_control_policy_id = self.env["credit.control.policy"].create(
            {
                "name": "Always Test Policy",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Always",
                            "rule": "always",
                            "classification_id": self.classification_accounts.id,
                        },
                    )
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
            UserError,
            msg="SO should not be confirmed when policy is always and action is block",
        ):
            sale_order_id.action_confirm()
