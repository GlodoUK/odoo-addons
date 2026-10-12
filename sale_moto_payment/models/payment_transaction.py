from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    is_moto = fields.Boolean(default=False)

    # XXX: disable missing-return is ok in 19.0 as nothing is returned upstream
    def _post_process(self):  # pylint: disable=missing-return
        moto = self.filtered("is_moto")
        if moto:
            super(
                PaymentTransaction, moto.with_context(skip_moto_payment_mail=True)
            )._post_process()
        if self - moto:
            super(PaymentTransaction, self - moto)._post_process()
