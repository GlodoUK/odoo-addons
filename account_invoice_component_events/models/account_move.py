from odoo import models

VALID_MOVE_TYPES = ["in_invoice", "in_refund", "out_invoice", "out_refund"]


class AccountMove(models.Model):
    _inherit = "account.move"

    def button_cancel(self):
        res = super().button_cancel()

        for move in self.filtered(lambda m: m.move_type in VALID_MOVE_TYPES):
            event = f"on_{move.move_type}_cancel"
            self._event(event).notify(move)

        return res

    def _invoice_paid_hook(self):
        res = super()._invoice_paid_hook()

        for move in self.filtered(lambda m: m.move_type in VALID_MOVE_TYPES):
            event = f"on_{move.move_type}_paid"
            self._event(event).notify(move)

        return res

    def _post(self, soft=True):
        posted = super()._post(soft=soft)

        for move in self.filtered(lambda m: m.move_type in VALID_MOVE_TYPES):
            event = f"on_{move.move_type}_open"
            self._event(event).notify(move)

        return posted
