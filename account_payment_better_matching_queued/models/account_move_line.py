from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def partial_reconcile_queued(
        self, payment_move, writeoff_acc_id=False, writeoff_journal_id=False
    ):
        self.partial_reconcile(payment_move, writeoff_acc_id, writeoff_journal_id)
