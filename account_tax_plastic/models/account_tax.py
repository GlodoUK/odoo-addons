from odoo import api, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    def _eval_taxes_computation_prepare_product_fields(self):
        # EXTENDS 'account_tax_python'
        # Ensures plastic_weight is always in the product evaluation context
        # so formulas can reference it without relying solely on formula parsing.
        return super()._eval_taxes_computation_prepare_product_fields() | {
            "plastic_weight"
        }

    @api.model
    def _eval_taxes_computation_prepare_product_values(
        self, default_product_values, product=None
    ):
        # EXTENDS 'account'
        # Formulas see plastic_weight in kg, whatever the system weight unit.
        values = super()._eval_taxes_computation_prepare_product_values(
            default_product_values, product=product
        )
        if values.get("plastic_weight"):
            values["plastic_weight"] = self.env[
                "product.template"
            ]._plastic_weight_to_kg(values["plastic_weight"])
        return values
