from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.template"

    alternative_ids = fields.Many2many(
        "product.product",
        "stock_variant_backups",
        "product_id",
        "backup_id",
        help="Product alternatives",
        string="Alternatives",
    )


class ProductTemplate(models.Model):
    _inherit = "product.product"

    stock_backup_ids = fields.Many2many(
        help="Product alternatives",
        string="Alternatives",
        related="product_tmpl_id.alternative_ids",
    )
