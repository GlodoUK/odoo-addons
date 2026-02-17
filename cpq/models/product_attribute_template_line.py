from odoo import fields, models


class ProductTemplateAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    cpq_propagate_to_variant = fields.Boolean(
        related="attribute_id.cpq_propagate_to_variant",
        store=True,
    )

    def _cpq_get_combination_info(self):
        self.ensure_one()

        ptav_active_ids = self.product_template_value_ids.filtered(
            lambda attr_line: attr_line.ptav_active
        )

        return {
            "id": self.id,
            "name": self.display_name,
            "display_type": self.attribute_id.display_type,
            "ptav_ids": [ ptav_id._cpq_get_combination_info() for ptav_id in ptav_active_ids ],
        }
