from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    max_line_sequence = fields.Integer(
        string="Max Line Sequence",
        compute="_compute_max_line_sequence",
        store=True,
    )

    @api.depends("order_line")
    def _compute_max_line_sequence(self):
        for order in self:
            current_max_line_sequence = order.max_line_sequence
     
            order_lines = order.order_line.filtered(lambda l: not l.display_type)

            order.max_line_sequence = max(
                current_max_line_sequence,
                max(order_lines.mapped("line_sequence"), default=0) + 1
            )
