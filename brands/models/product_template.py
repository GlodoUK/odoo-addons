from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_id = fields.Many2one(
        "glo.brand",
        help="Select a brand for this product",
    )
