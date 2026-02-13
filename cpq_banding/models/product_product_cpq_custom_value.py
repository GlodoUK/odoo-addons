from odoo import api, models


class ProductAttributeCustomValue(models.Model):
    _inherit = "product.product.cpq.custom.value"

    @api.depends("custom_value", "ptav_id.display_name")
    def _compute_name(self):
        res = super()._compute_name()

        for value in self.filtered(lambda v: v.ptav_id.cpq_custom_type == "banding"):
            banding = value.ptav_id.product_attribute_value_id._cpq_cast_custom_banding(
                value.custom_value
            )
            if banding:
                value.name = f"{value.ptav_id.display_name}: {banding.display_name}"

        return res
