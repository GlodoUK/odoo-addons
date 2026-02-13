from odoo import fields, models


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    cpq_banding_id = fields.Many2one(
        related="product_attribute_value_id.cpq_banding_id"
    )

    def _cpq_get_combination_info(self):
        res = super()._cpq_get_combination_info()

        if self.is_custom and self.cpq_custom_type == "banding":
            res.update(
                {
                    "cpq_selection_values": [
                        (b.id, b.display_name)
                        for b in self.env["cpq.banding"].search(
                            [
                                ("parent_id", "child_of", self.cpq_banding_id.id),
                                ("is_leaf", "=", True),
                            ]
                        )
                    ]
                }
            )

        return res
