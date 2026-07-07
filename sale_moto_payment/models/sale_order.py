from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _send_payment_succeeded_for_order_mail(self):
        if self.env.context.get("skip_moto_payment_mail"):
            return
        return super()._send_payment_succeeded_for_order_mail()

    def _send_order_confirmation_mail(self):
        if self.env.context.get("skip_moto_payment_mail"):
            return
        return super()._send_order_confirmation_mail()
