from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    has_cpq_phantom = fields.Boolean(compute="_compute_has_cpq_phantom", store=True)

    @api.depends("move_lines")
    def _compute_has_cpq_phantom(self):
        for picking_id in self:
            picking_id.has_cpq_phantom = any(picking_id.move_lines.mapped("cpq_bom_id"))
