from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    quotation_only = fields.Boolean()
