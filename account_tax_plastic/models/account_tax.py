from odoo import models


class AccountTax(models.Model):
    _inherit = "account.tax"

    def _eval_taxes_computation_prepare_product_fields(self):
        # EXTENDS 'account_tax_python'
        # Ensures plastic_weight is always in the product evaluation context
        # so formulas can reference it without relying solely on formula parsing.
        return super()._eval_taxes_computation_prepare_product_fields() | {
            "plastic_weight"
        }
