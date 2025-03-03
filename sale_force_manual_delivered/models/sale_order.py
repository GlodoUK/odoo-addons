from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    force_manual_delivered_qty = fields.Boolean(default=False)

    @api.depends("force_manual_delivered_qty", "is_expense", "state")
    def _compute_qty_delivered_method(self):
        res = super()._compute_qty_delivered_method()
        for line in self.filtered(
            lambda order_line: order_line.force_manual_delivered_qty
        ):
            if line.force_manual_delivered_qty:
                line.qty_delivered_method = "manual"
        return res
