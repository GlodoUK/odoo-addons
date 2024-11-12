from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    product_tmpl_meta_line_parent_id = fields.Many2one(
        related="sale_line_id.meta_tmpl_line_id.parent_id",
        string="Meta Product Parent",
        store=True,
    )
