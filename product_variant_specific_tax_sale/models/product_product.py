from odoo import api, fields, models


class Product(models.Model):
    _inherit = "product.product"

    taxes_id = fields.Many2many(
        "account.tax",
        "product_product_taxes_rel",
        "prod_id",
        "tax_id",
        compute="_compute_taxes_id",
        inverse="_inverse_taxes_id",
        store=True,
        string="Sales Taxes",
    )

    variant_taxes_id = fields.Many2many(
        "account.tax",
        "product_product_variant_taxes_rel",
        "prod_id",
        "tax_id",
        domain=[("type_tax_use", "=", "sale")],
        string="Variant Sales Taxes",
    )

    @api.depends("product_tmpl_id.taxes_id", "variant_taxes_id")
    def _compute_taxes_id(self):
        for product in self:
            product.taxes_id = (
                product.variant_taxes_id or product.product_tmpl_id.taxes_id
            )

    def _inverse_taxes_id(self):
        for product in self:
            product.product_tmpl_id.taxes_id = product.taxes_id
