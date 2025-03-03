from odoo import models, api
from odoo.addons.queue_job.job import job


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @job(default_channel='root.account_move_line_reconcile_queued')
    @api.multi
    def partial_reconcile_queued(self, payment_move, writeoff_acc_id=False, writeoff_journal_id=False):
        self.partial_reconcile(payment_move, writeoff_acc_id, writeoff_journal_id)
