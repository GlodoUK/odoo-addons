from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    has_commingled = fields.Boolean(compute="_compute_has_commingled")

    @api.depends("move_lines")
    def _compute_has_commingled(self):
        for picking in self:
            picking.has_commingled = any(
                picking.move_lines.mapped("commingled_original_product_id")
            )
