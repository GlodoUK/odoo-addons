from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    cpq_description_sale_tmpl = fields.Text("Configurable Sale Description Template")
