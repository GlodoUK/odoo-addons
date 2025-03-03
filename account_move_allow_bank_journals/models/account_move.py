from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_suitable_journal_ids(self):
        res = super()._compute_suitable_journal_ids()

        bank_journal_ids = self.env["account.journal"].search([("type", "=", "bank")])

        for record in self.filtered(lambda m: not m.invoice_filter_type_domain):
            record.suitable_journal_ids |= bank_journal_ids

        return res
