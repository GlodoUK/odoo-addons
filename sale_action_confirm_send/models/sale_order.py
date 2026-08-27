from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm_send(self):
        return self.with_context(send_email=True).action_confirm()
