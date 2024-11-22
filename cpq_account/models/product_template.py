from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _cpq_get_create_variant_vals(self, pta_value_ids, custom_dict=None):
        res = super()._cpq_get_create_variant_vals(pta_value_ids, custom_dict)
        res.update(
            {
                "taxes_id": [(6, 0, self.taxes_id.ids)],
            }
        )
        return res
