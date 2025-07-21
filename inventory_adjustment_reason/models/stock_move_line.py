from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    note = fields.Text(
        related="move_id.note",
    )
