from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    spring_carrier = fields.Char()
    spring_tracking_url = fields.Char()
