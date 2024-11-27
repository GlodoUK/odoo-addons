from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def action_post(self):
        result = super(AccountInvoice, self).action_post()

        for inv in self:
            if inv.move_type not in [
                "out_invoice",
                "out_refund",
                "in_invoice",
                "in_refund",
            ]:
                continue
            # Turn it into the format on_out_open, for customer
            # invoice, for example
            # See account.invoice for types
            event = "on_%s_open" % (inv.move_type)
            self._event(event).notify(inv)

        return result

    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        for record in self:
            event = "on_%s_paid" % (record.move_type)
            self._event(event).notify(record)
        return res

    def button_cancel(self):
        res = super(AccountInvoice, self).button_cancel()
        for record in self:
            event = "on_%s_cancel" % (record.move_type)
            self._event(event).notify(record)
        return res
