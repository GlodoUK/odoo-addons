from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    customer_ref = fields.Char(string="Customer Reference")
