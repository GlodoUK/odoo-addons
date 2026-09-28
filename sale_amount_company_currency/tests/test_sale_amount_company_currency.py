from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestSaleAmountCompanyCurrency(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.currency_gbp = cls.env.ref("base.GBP")
        cls.currency_usd = cls.env.ref("base.USD")

        cls.company_id = cls.env.company

        cls.env["res.currency.rate"].search([]).unlink()

        cls.env["res.currency.rate"].create(
            [
                {
                    "name": fields.Date.today(),
                    "company_id": cls.company_id.id,
                    "currency_id": cls.currency_usd.id,
                    "rate": 1.0,
                },
                {
                    "name": fields.Date.today(),
                    "company_id": cls.company_id.id,
                    "currency_id": cls.currency_gbp.id,
                    "rate": 0.5,
                },
            ]
        )

        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

        cls.tax_10 = cls.env["account.tax"].create(
            {
                "name": "10% Test Tax",
                "amount_type": "percent",
                "amount": 10.0,
                "type_tax_use": "sale",
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "list_price": 100.0,
                "taxes_id": [Command.set([cls.tax_10.id])],
            }
        )

        cls.pricelist_usd = cls.env["product.pricelist"].create(
            {
                "name": "USD Pricelist",
                "currency_id": cls.currency_usd.id,
            }
        )

        cls.pricelist_gbp = cls.env["product.pricelist"].create(
            {
                "name": "GBP Pricelist",
                "currency_id": cls.currency_gbp.id,
            }
        )

    def test_same_currency(self):
        """
        $100 + 10% tax = $110 total, $100 untaxed
        Company currency is USD, so no conversion needed.
        """
        sale_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist_usd.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "price_unit": 100.0,
                        }
                    ),
                ],
            }
        )

        self.assertEqual(sale_id.amount_untaxed, 100.0)
        self.assertEqual(sale_id.amount_tax, 10.0)
        self.assertEqual(sale_id.amount_total, 110.0)
        self.assertEqual(sale_id.amount_untaxed_company, 100.0)
        self.assertEqual(sale_id.amount_tax_company, 10.0)
        self.assertEqual(sale_id.amount_total_company, 110.0)

    def test_conversion(self):
        """
        £100 + £200 = £300 untaxed, + 10% tax = £330 total
        At rate 0.5: $600 untaxed, $660 total
        """
        sale_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist_gbp.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "price_unit": 100.0,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "price_unit": 200.0,
                        }
                    ),
                ],
            }
        )

        self.assertEqual(sale_id.amount_untaxed, 300.0)
        self.assertEqual(sale_id.amount_tax, 30.0)
        self.assertEqual(sale_id.amount_total, 330.0)
        self.assertEqual(sale_id.amount_untaxed_company, 600.0)
        self.assertEqual(sale_id.amount_tax_company, 60.0)
        self.assertEqual(sale_id.amount_total_company, 660.0)
