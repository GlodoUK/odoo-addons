from odoo import models, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def open_payment_matching_screen_better(self):
        self.ensure_one()

        # Open reconciliation view for customers/suppliers
        move_line_id = False
        for move_line in self.move_line_ids:
            if move_line.account_id.reconcile:
                move_line_id = move_line.id
                break
        if not self.partner_id:
            raise UserError(_("Payments without a partner can't be matched"))

        if not move_line_id:
            raise UserError(_("No move needing to be reconcilced"))

        return {
            "view_type": "form",
            "view_mode": "form",
            "view_id": self.env.ref(
                "account_payment_better_matching.account_payment_better_matching_form"
            ).id,
            "res_model": "account.payment.better.matching",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {"default_payment_id": self.id,},
            "name": _("Payment Matching"),
        }

    def open_payment_matching_screen_result(self):
        self.ensure_one()
        [action] = self.env.ref("account.action_account_moves_all_a").read()
        ids = []
        for aml in self.mapped("move_line_ids"):
            if aml.account_id.reconcile:
                ids.extend(
                    [r.debit_move_id.id for r in aml.matched_debit_ids]
                    if aml.credit > 0
                    else [r.credit_move_id.id for r in aml.matched_credit_ids]
                )
                ids.append(aml.id)
        action["domain"] = [("id", "in", ids)]
        return action
