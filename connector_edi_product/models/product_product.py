from odoo import api, fields, models
from odoo.osv import expression

PRODUCT_EVENT_MONITOR_FIELDS = [
    "active",
    "barcode",
    "default_code",
    "description",
    "description_sale",
    "categ_id",
    "image_1920",
    "list_price",
    "name",
    "sale_ok",
    "taxes_id",
    "type",
    "weight",
]


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "edi.message.mixin"]

    edi_product_ids = fields.One2many(
        "edi.product.product",
        "odoo_id",
        copy=False,
    )

    edi_product_count = fields.Integer(
        compute="_compute_edi_product_count",
        store=True,
    )

    @api.depends("edi_product_ids")
    def _compute_edi_product_count(self):
        for product in self:
            product.edi_product_count = len(product.edi_product_ids)

    @api.model
    def create(self, vals):
        res = super().create(vals)

        if any(monitor_field in vals for monitor_field in self._get_monitor_fields()):
            if self.env.context.get("skip_edi_push", False):
                return res

            for product in res:
                product._event("on_record_create_edi").notify(product)

        return res

    def write(self, vals):
        res = super().write(vals)

        if any(monitor_field in vals for monitor_field in self._get_monitor_fields()):
            if self.env.context.get("skip_edi_push", False):
                return res

            for product in self:
                product._event("on_record_write_edi").notify(product)

        return res

    def _edi_message_ids_domain(self):
        extra_domain = [
            ("model", "=", "edi.product.product"),
            ("res_id", "in", self.edi_product_ids.ids),
        ]

        return expression.OR(
            [
                super()._edi_message_ids_domain(),
                extra_domain,
            ]
        )

    @api.model
    def _get_monitor_fields(self):
        return PRODUCT_EVENT_MONITOR_FIELDS
