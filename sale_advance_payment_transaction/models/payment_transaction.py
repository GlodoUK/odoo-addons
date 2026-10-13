from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _create_payment(self, **extra_create_values):
        # Only a single order is unambiguous; core doesn't support grouped
        # order payments either.
        if len(self.sale_order_ids) == 1:
            extra_create_values.setdefault("sale_id", self.sale_order_ids.id)
        return super()._create_payment(**extra_create_values)
