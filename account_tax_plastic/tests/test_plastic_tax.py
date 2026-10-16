from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

LB_IN_KG = 0.45359237


@tagged("post_install", "-at_install")
class TestPlasticTax(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write(
            {
                "plastic_tax_rate": 0.30,
                "plastic_tax_currency_id": cls.company.currency_id.id,
            }
        )
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Plastic Tax",
                "amount_type": "code",
                "formula": "product.plastic_weight * quantity * 1.0",
                "company_id": cls.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Plastic Widget", "plastic_weight": 10.0}
        )

    def _set_weight_in_lbs(self, in_lbs):
        self.env["ir.config_parameter"].sudo().set_param(
            "product.weight_in_lbs", "1" if in_lbs else "0"
        )

    def _shipment_tax(self):
        return self.company._get_plastic_tax(
            10.0, 20.0, self.company.currency_id, "2026-01-01"
        )

    def _formula_tax(self):
        res = self.tax.compute_all(100.0, quantity=2.0, product=self.product)
        return sum(t["amount"] for t in res["taxes"])

    def test_shipment_kg(self):
        self._set_weight_in_lbs(False)
        self.assertAlmostEqual(self._shipment_tax(), 3.0, places=2)
        self.company.plastic_tax_basis = "gross_weight"
        self.assertAlmostEqual(self._shipment_tax(), 6.0, places=2)

    def test_shipment_lb(self):
        self._set_weight_in_lbs(True)
        self.assertAlmostEqual(self._shipment_tax(), 10 * LB_IN_KG * 0.30, places=2)

    def test_formula_kg(self):
        self._set_weight_in_lbs(False)
        self.assertAlmostEqual(self._formula_tax(), 20.0, places=2)

    def test_formula_lb(self):
        self._set_weight_in_lbs(True)
        self.assertAlmostEqual(self._formula_tax(), 20 * LB_IN_KG, places=2)
