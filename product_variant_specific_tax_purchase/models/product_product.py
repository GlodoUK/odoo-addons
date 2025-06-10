from odoo import api, fields, models


class Product(models.Model):
    _inherit = "product.product"

    supplier_taxes_id = fields.Many2many(
        "account.tax",
        "product_product_supplier_taxes_rel",
        "prod_id",
        "tax_id",
        compute="_compute_supplier_taxes_id",
        inverse="_inverse_supplier_taxes_id",
        store=True,
        string="Purchase Taxes",
    )

    variant_supplier_taxes_id = fields.Many2many(
        "account.tax",
        "product_product_variant_supplier_taxes_rel",
        "prod_id",
        "tax_id",
        domain=[("type_tax_use", "=", "purchase")],
        string="Variant Purchase Taxes",
    )

    @api.depends("product_tmpl_id.supplier_taxes_id", "variant_supplier_taxes_id")
    def _compute_supplier_taxes_id(self):
        for product in self:
            product.supplier_taxes_id = (
                product.variant_supplier_taxes_id
                or product.product_tmpl_id.supplier_taxes_id
            )

    def _inverse_supplier_taxes_id(self):
        for product in self:
            product.product_tmpl_id.supplier_taxes_id = product.supplier_taxes_id
