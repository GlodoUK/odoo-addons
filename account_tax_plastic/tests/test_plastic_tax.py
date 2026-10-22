from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

LB_IN_KG = 0.45359237


@tagged("post_install", "-at_install")
class TestPlasticTax(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
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

    def _formula_tax(self):
        res = self.tax.compute_all(100.0, quantity=2.0, product=self.product)
        return sum(t["amount"] for t in res["taxes"])

    def test_formula_kg(self):
        self._set_weight_in_lbs(False)
        self.assertAlmostEqual(self._formula_tax(), 20.0, places=2)

    def test_formula_lb(self):
        self._set_weight_in_lbs(True)
        self.assertAlmostEqual(self._formula_tax(), 20 * LB_IN_KG, places=2)
