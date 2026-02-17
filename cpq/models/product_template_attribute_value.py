from odoo import fields, models


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    cpq_custom_type = fields.Selection(
        related="product_attribute_value_id.cpq_custom_type"
    )

    cpq_propagate_to_variant = fields.Boolean(
        related="attribute_id.cpq_propagate_to_variant"
    )

    def _cpq_get_combination_info(self):
        self.ensure_one()

        return {
            "id": self.id,
            "name": self.name,
            "html_color": self.html_color,
            "is_custom": self.is_custom,
            "price_extra": 0.0,
            "excluded": False,
            "cpq_custom_type": self.cpq_custom_type,
        }
