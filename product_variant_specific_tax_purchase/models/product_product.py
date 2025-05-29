from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    variant_supplier_taxes_id = fields.Many2many(
        "account.tax",
        domain=[("type_tax_use", "=", "purchase")],
        help="Additional purchase taxes specific to this variant",
        string="Variant Purchase Taxes",
    )
