from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        res.update({"hold": self.sale_line_id.order_id.hold})
        return res
