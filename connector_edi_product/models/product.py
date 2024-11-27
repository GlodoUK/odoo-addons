from odoo import api, fields, models
from odoo.osv import expression

PRODUCT_EVENT_MONITOR_FIELDS = [
    "name",
    "default_code",
    "barcode",
    "type",
    "categ_id",
    "sale_ok",
    "active",
    "description",
    "description_sale",
    "list_price",
    "weight",
    "taxes_id",
    "image_1920",
]


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "edi.message.mixin"]

    edi_product_tmpl_ids = fields.One2many(
        "edi.product.template",
        "odoo_id",
        copy=False,
    )
    edi_product_ids = fields.One2many(
        related="product_variant_ids.edi_product_ids",
    )

    edi_product_count = fields.Integer(compute="_compute_edi_product_count", store=True)

    @api.depends("edi_product_tmpl_ids", "product_variant_ids.edi_product_ids")
    def _compute_edi_product_count(self):
        for record in self:
            record.edi_product_count = len(record.edi_product_ids) + len(
                record.edi_product_tmpl_ids
            )

    def _get_monitor_fields(self):
        return PRODUCT_EVENT_MONITOR_FIELDS

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res and any(field in vals for field in res._get_monitor_fields()):
            res._event("on_record_create_edi").notify(res)

        return res

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in self._get_monitor_fields()):
            if self.env.context.get("skip_edi_push", False):
                return res

            for record in self:
                record._event("on_record_write_edi").notify(record)

            for record in self:
                for product in record.product_variant_ids:
                    product._event("on_record_write_edi").notify(product)
        return res


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "edi.message.mixin"]

    edi_product_ids = fields.One2many(
        "edi.product.product",
        "odoo_id",
        copy=False,
    )

    edi_product_count = fields.Integer(compute="_compute_edi_product_count", store=True)

    @api.depends("edi_product_ids")
    def _compute_edi_product_count(self):
        for record in self:
            record.edi_product_count = len(record.edi_product_ids)

    def _edi_message_ids_domain(self):
        return expression.OR(
            [
                super()._edi_message_ids_domain(),
                [
                    ("model", "=", "edi.product.product"),
                    ("res_id", "in", self.edi_product_ids.ids),
                ],
            ]
        )

    def _get_monitor_fields(self):
        return PRODUCT_EVENT_MONITOR_FIELDS

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in self._get_monitor_fields()):
            if self.env.context.get("skip_edi_push", False):
                return res
            for record in self:
                record._event("on_record_write_edi").notify(record)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for vals in vals_list:
            if any(field in vals for field in self._get_monitor_fields()):
                if self.env.context.get("skip_edi_push", False):
                    return res
                for record in res:
                    record._event("on_record_create_edi").notify(record)
        return res
