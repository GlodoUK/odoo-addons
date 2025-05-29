from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    variant_supplier_taxes_id = fields.Many2many(
        "account.tax",
        domain=[("type_tax_use", "=", "purchase")],
        help="These are used instead of purchase taxes set on the template.",
        string="Variant Purchase Taxes",
    )
