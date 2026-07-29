from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_package_carrier_type_for_pack(self):
        res = super()._get_package_carrier_type_for_pack()
        return "none" if res == "base_on_code" else res
