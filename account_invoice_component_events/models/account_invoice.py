from odoo import models

VALID_MOVE_TYPES = ["out_invoice", "out_refund", "in_invoice", "in_refund"]


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        result = super()._post(soft=soft)
        for inv in self.filtered(lambda m: m.move_type in VALID_MOVE_TYPES):
            event = "on_%s_open" % (inv.move_type)
            self._event(event).notify(inv)
        return result

    def action_invoice_paid(self):
        result = super().action_invoice_paid()
        for record in self.filtered(lambda m: m.move_type in VALID_MOVE_TYPES):
            event = "on_%s_paid" % (record.move_type)
            self._event(event).notify(record)
        return result

    def button_cancel(self):
        result = super().button_cancel()
        for record in self.filtered(lambda m: m.move_type in VALID_MOVE_TYPES):
            event = "on_%s_cancel" % (record.move_type)
            self._event(event).notify(record)
        return result
