from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_report_base_filename(self):
        self.ensure_one()
        return "%s" % self.name
