from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_reconciled = fields.Boolean(compute="_compute_payment_reconciled")

    def _compute_payment_reconciled(self):
        for record in self:
            line = record._get_payment_line()
            record.payment_reconciled = line and line.amount_residual == 0

    def _get_payment_line(self):
        self.ensure_one()
        move_line_id = self.env["account.move.line"]
        if self.payment_type == "outbound":
            move_line_id = self.line_ids.filtered(
                lambda r: r.account_id.reconcile and r.debit > 0
            )
        else:
            move_line_id = self.line_ids.filtered(
                lambda r: r.account_id.reconcile and r.credit > 0
            )
        return move_line_id

    def open_payment_matching_screen_better(self):
        self.ensure_one()

        # Open reconciliation view for customers/suppliers
        move_line_id = self._get_payment_line().id
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
            "context": {
                "default_payment_id": self.id,
            },
            "name": _("Payment Matching"),
        }

    def open_payment_matching_screen_result(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_account_moves_all_a"
        )
        ids = []
        for aml in self.mapped("line_ids"):
            if aml.account_id.reconcile:
                ids.extend(
                    [r.debit_move_id.id for r in aml.matched_debit_ids]
                    if aml.credit > 0
                    else [r.credit_move_id.id for r in aml.matched_credit_ids]
                )
                ids.append(aml.id)
        action["domain"] = [("id", "in", ids)]
        return action
