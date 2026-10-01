from odoo import models


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move", "product_fsc.line.mixin"]
