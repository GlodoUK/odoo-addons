from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPurchase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        # Unless otherwise specified this will only work with
        # the l10 generic coa, as per upstream
        super(TestPurchase, cls).setUpClass(chart_template_ref)

        cls.partner_purchase_journal = cls.env["account.journal"].create(
            {
                "name": "Partner Journal",
                "code": "PJ",
                "type": "purchase",
            }
        )

        uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product_switch = cls.env["product.product"].create(
            {
                "name": "Switch, 24 ports",
                "standard_price": 55.0,
                "list_price": 70.0,
                "type": "consu",
                "uom_id": uom_unit.id,
                "uom_po_id": uom_unit.id,
                "purchase_method": "purchase",
                "default_code": "PROD_24SWITCH",
                "taxes_id": False,
            }
        )

    def test_normal_vendor_bill(self):
        purchase_order = (
            self.env["purchase.order"]
            .with_context(tracking_disable=True)
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "name": self.product_switch.name,
                                "product_id": self.product_switch.id,
                                "product_qty": 10.0,
                                "product_uom": self.product_switch.uom_id.id,
                                "price_unit": self.product_switch.list_price,
                                "taxes_id": False,
                            },
                        )
                    ],
                }
            )
        )
        purchase_order.button_confirm()
        purchase_order.action_create_invoice()

        am = (
            self.env["account.move.line"]
            .search([("purchase_line_id", "=", purchase_order.order_line.id)])
            .move_id
        )

        self.assertEqual(am.journal_id, self.company_data["default_journal_purchase"])

    def test_forced_vendor_bill(self):
        self.partner_a.property_purchase_journal_id = self.partner_purchase_journal

        purchase_order = (
            self.env["purchase.order"]
            .with_context(tracking_disable=True)
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "name": self.product_switch.name,
                                "product_id": self.product_switch.id,
                                "product_qty": 10.0,
                                "product_uom": self.product_switch.uom_id.id,
                                "price_unit": self.product_switch.list_price,
                                "taxes_id": False,
                            },
                        )
                    ],
                }
            )
        )
        purchase_order.button_confirm()
        purchase_order.action_create_invoice()

        am = (
            self.env["account.move.line"]
            .search([("purchase_line_id", "=", purchase_order.order_line.id)])
            .move_id
        )

        self.assertEqual(am.journal_id, self.partner_purchase_journal)
