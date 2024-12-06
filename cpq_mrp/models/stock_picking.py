from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    has_cpq_phantom = fields.Boolean(compute="_compute_has_cpq_phantom", store=True)

    @api.depends("move_ids")
    def _compute_has_cpq_phantom(self):
        for picking_id in self:
            # Check if any move has a CPQ BOM
            picking_id.has_cpq_phantom = any(picking_id.move_ids.mapped("cpq_bom_id"))
