from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    cpq_description = fields.Char(related="move_id.cpq_description")
    has_cpq_phantom = fields.Boolean(related="picking_id.has_cpq_phantom")
