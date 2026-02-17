from odoo import fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    cpq_propagate_to_variant = fields.Boolean(
        "Propagate To Variant",
        default=True,
    )
