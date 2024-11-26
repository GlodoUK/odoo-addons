from odoo import api, models


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    @api.onchange("product_id")
    def _onchange_set_apply_variant(self):
        if self.product_id:
            component_att_values = (
                self.product_id.product_template_attribute_value_ids.mapped(
                    "product_attribute_value_id"
                )
            )
            product_tmpl_att_lines = (
                self.bom_id.product_tmpl_id.valid_product_template_attribute_line_ids
            )
            product_tmpl_att_values = product_tmpl_att_lines.mapped(
                "product_template_value_ids"
            )
            component_apply_att_values = product_tmpl_att_values.filtered(
                lambda tmpl_att_value: tmpl_att_value.product_attribute_value_id.id
                in component_att_values.ids
            )
            self.bom_product_template_attribute_value_ids = [
                (6, 0, component_apply_att_values.ids)
            ]
