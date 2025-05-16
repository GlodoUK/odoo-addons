from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    edi_sale_order_line_ids = fields.One2many(
        "edi.sale.order.line",
        "odoo_id",
    )

    edi_sale_order_line_count = fields.Integer(
        compute="_compute_edi_sale_order_line_count",
        store=True,
    )

    @api.depends("edi_sale_order_line_ids")
    def _compute_edi_sale_order_line_count(self):
        for line in self:
            line.edi_sale_order_line_count = len(line.edi_sale_order_line_ids)
