from odoo import api, fields, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "edi.message.mixin"]

    edi_sale_order_ids = fields.One2many(
        "edi.sale.order",
        "odoo_id",
        copy=False,
    )

    edi_sale_order_count = fields.Integer(
        compute="_compute_edi_sale_order_count", store=True
    )

    @api.depends("edi_sale_order_ids")
    def _compute_edi_sale_order_count(self):
        for record in self:
            record.edi_sale_order_count = len(record.edi_sale_order_ids)

    def _edi_message_ids_domain(self):
        return expression.OR(
            [
                super()._edi_message_ids_domain(),
                [
                    ("model", "=", "edi.sale.order"),
                    ("res_id", "in", self.edi_sale_order_ids.ids),
                ],
            ]
        )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    edi_sale_order_line_ids = fields.One2many("edi.sale.order.line", "odoo_id")

    edi_sale_order_line_count = fields.Integer(
        compute="_compute_edi_sale_order_line_count", store=True
    )

    @api.depends("edi_sale_order_line_ids")
    def _compute_edi_sale_order_line_count(self):
        for record in self:
            record.edi_sale_order_line_count = len(record.edi_sale_order_line_ids)
