from odoo import models, _
from odoo.exceptions import UserError


class AccountPaymentBetterMatching(models.TransientModel):
    _inherit = 'account.payment.better.matching'

    def process_queued(self):
        if not self.partner_id:
            raise UserError(_("Payments without a partner can't be matched"))

        if not self.move_line_id:
            raise UserError(_("No move needing to be reconcilced"))

        if not self.matched_move_line_ids:
            raise UserError(_("No moves selected for reconciliation"))

        records = self.env['account.move.line']

        records |= self.move_line_id
        records |= self.matched_move_line_ids

        if self.partial_reconcile:
            records.sudo().with_delay().partial_reconcile_queued(self.move_line_id)
        else:
            records.sudo().with_delay().reconcile_queued()

