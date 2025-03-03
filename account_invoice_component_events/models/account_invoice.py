from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        result = super(AccountInvoice, self).action_invoice_open()

        for inv in self:
            # Turn it into the format on_out_open, for customer
            # invoice, for example
            # See account.invoice for types
            event = "on_%s_open" % (inv.type)
            self._event(event).notify(inv)

        return result

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        for record in self:
            event = "on_%s_paid" % (record.type)
            self._event(event).notify(record)
        return res

    @api.multi
    def action_invoice_cancel(self):
        res = super(AccountInvoice, self).action_invoice_cancel()
        for record in self:
            event = "on_%s_cancel" % (record.type)
            self._event(event).notify(record)
        return res
