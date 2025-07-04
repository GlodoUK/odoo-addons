from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    force_manual_delivered_qty = fields.Boolean()

    @api.depends("force_manual_delivered_qty")
    def _compute_qty_delivered_method(self):
        manual_lines = self.filtered("force_manual_delivered_qty")
        manual_lines.qty_delivered_method = "manual"
        return super(SaleOrderLine, self - manual_lines)._compute_qty_delivered_method()
