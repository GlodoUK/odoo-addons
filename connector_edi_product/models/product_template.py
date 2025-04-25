from odoo import api, fields, models

from .product_product import PRODUCT_EVENT_MONITOR_FIELDS


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "edi.message.mixin"]

    edi_product_ids = fields.One2many(
        related="product_variant_ids.edi_product_ids",
    )

    edi_product_tmpl_ids = fields.One2many(
        "edi.product.template",
        "odoo_id",
        copy=False,
    )

    edi_product_count = fields.Integer(
        compute="_compute_edi_product_count",
        store=True,
    )

    @api.depends("edi_product_tmpl_ids", "product_variant_ids.edi_product_ids")
    def _compute_edi_product_count(self):
        for product_tmpl in self:
            product_tmpl.edi_product_count = len(product_tmpl.edi_product_ids) + len(
                product_tmpl.edi_product_tmpl_ids
            )

    @api.model
    def create(self, vals):
        res = super().create(vals)

        if any(monitor_field in vals for monitor_field in self._get_monitor_fields()):
            if self.env.context.get("skip_edi_push", False):
                return res

            for product_tmpl in res:
                product_tmpl._event("on_record_create_edi").notify(product_tmpl)

        return res

    def write(self, vals):
        res = super().write(vals)

        if any(monitor_field in vals for monitor_field in self._get_monitor_fields()):
            if self.env.context.get("skip_edi_push", False):
                return res

            for product_tmpl in self:
                product_tmpl._event("on_record_write_edi").notify(product_tmpl)

        return res

    @api.model
    def _get_monitor_fields(self):
        return PRODUCT_EVENT_MONITOR_FIELDS
