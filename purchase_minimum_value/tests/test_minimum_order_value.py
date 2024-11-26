# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("-at_install", "post_install")
class TestPurchase(AccountTestInvoicingCommon):
    def test_no_minimum_value(self):
        self.partner_a.property_minimum_purchase_order_action = "none"
        purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "product_qty": 1.0,
                            "price_unit": 5.0,
                        },
                    )
                ],
            }
        )
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.state in ("purchase", "done"))

    def test_below_minimum_value(self):
        purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "product_qty": 1.0,
                            "price_unit": 5.0,
                        },
                    )
                ],
            }
        )
        self.partner_a.property_minimum_purchase_order_action = "block"
        self.partner_a.property_minimum_purchase_order_value = "99.99"
        self.partner_a.property_minimum_purchase_order_currency_id = (
            purchase_order.currency_id
        )

        with self.assertRaises(UserError):
            purchase_order.button_confirm()

    def test_above_minimum_value(self):
        purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "product_qty": 1.0,
                            "price_unit": 5.0,
                        },
                    )
                ],
            }
        )
        self.partner_a.property_minimum_purchase_order_action = "block"
        self.partner_a.property_minimum_purchase_order_value = "0.01"
        self.partner_a.property_minimum_purchase_order_currency_id = (
            purchase_order.currency_id
        )

        purchase_order.button_confirm()
        self.assertTrue(purchase_order.state in ("purchase", "done"))
