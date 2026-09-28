from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    skip_send_to_shipper = fields.Boolean(default=False)

    def send_to_shipper(self):
        self.ensure_one()

        if self.skip_send_to_shipper:
            return

        return super().send_to_shipper()
