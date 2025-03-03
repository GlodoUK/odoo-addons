from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    commingled_ok = fields.Boolean(
        "Is Commingled?",
        compute="_compute_commingled_ok",
        inverse="_inverse_commingled_ok",
    )

    commingled_ids = fields.One2many(
        "product.commingled",
        compute="_compute_commingled",
        inverse="_inverse_commingled",
    )

    used_in_commingled_ids = fields.One2many(
        related="product_variant_ids.used_in_commingled_ids",
    )

    @api.depends("product_variant_ids.commingled_ok")
    def _compute_commingled_ok(self):
        for record in self:
            record.commingled_ok = all(
                v.commingled_ok for v in record.product_variant_ids
            )

    def _inverse_commingled_ok(self):
        for p in self:
            if len(p.product_variant_ids) == 1:
                p.product_variant_ids.commingled_ok = p.commingled_ok

    @api.depends("product_variant_ids", "product_variant_ids.commingled_ids")
    def _compute_commingled(self):
        for p in self:
            if len(p.product_variant_ids) == 1:
                p.commingled_ids = p.product_variant_ids.commingled_ids
            else:
                p.commingled_ids = False

    def _inverse_commingled(self):
        for p in self:
            if len(p.product_variant_ids) == 1:
                p.product_variant_ids.commingled_ids = p.commingled_ids
