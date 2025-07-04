from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def send_to_shipper(self):
        self.ensure_one()
        if self.carrier_id:
            self.carrier_id._ensure_valid_shipping(self)
        return super().send_to_shipper()
