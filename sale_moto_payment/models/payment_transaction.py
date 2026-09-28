from odoo import fields, models
from odoo.tools import str2bool


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    is_moto = fields.Boolean(default=False)

    # XXX: disable missing-return is ok in 19.0 as nothing is returned upstream
    def _post_process(self):  # pylint: disable=missing-return
        moto = self.filtered("is_moto")

        if moto:
            # Run super first: this calls _check_amount_and_confirm_order() which puts
            # draft/sent orders into 'sale' state before we try to invoice them.
            super(
                PaymentTransaction, moto.with_context(skip_moto_payment_mail=True)
            )._post_process()

            # When sale.automatic_invoice is off (e.g. "delivered qty" invoicing policy
            # hides that setting), super skipped invoice creation. Do it now that the
            # orders are confirmed, then post the resulting draft invoices directly.
            auto_invoice = str2bool(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("sale.automatic_invoice")
            )
            if not auto_invoice:
                for done_tx in moto.filtered(
                    lambda tx: tx.state == "done" and tx.operation != "validation"
                ):
                    done_tx._invoice_sale_orders()
                    done_tx.invoice_ids.filtered(
                        lambda inv: inv.state == "draft"
                    ).action_post()
                    # _force_lines_to_invoice_policy_order() was called inside
                    # _invoice_sale_orders() before the invoice existed. posting the
                    # invoice updates qty_invoiced, which triggers a recompute of the
                    # stored qty_to_invoice back to the delivered-policy value
                    # (qty_delivered - qty_invoiced), which goes negative for
                    # undelivered lines.
                    done_tx.sale_order_ids._force_lines_to_invoice_policy_order()

        if self - moto:
            super(PaymentTransaction, self - moto)._post_process()
