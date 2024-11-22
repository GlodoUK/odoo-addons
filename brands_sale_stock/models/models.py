from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    brand_id = fields.Many2one(
        related="group_id.sale_id.brand_id",
        string="Brand",
        store=True,
        readonly=False
    )
