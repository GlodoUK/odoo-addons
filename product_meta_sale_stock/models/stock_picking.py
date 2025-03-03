from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    has_meta_lines = fields.Boolean(compute="_compute_has_meta_lines", store=True)

    @api.depends("move_lines.product_tmpl_meta_line_parent_id")
    def _compute_has_meta_lines(self):
        for record in self:
            record.has_meta_lines = any(
                record.move_lines.mapped("product_tmpl_meta_line_parent_id")
            )
