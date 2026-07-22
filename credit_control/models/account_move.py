from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    skip_credit_control_rules = fields.Boolean(
        "Allow Credit Control Bypass",
        copy=False,
    )

    def action_post(self):
        for move in self:
            if move.move_type == "out_invoice":
                move._check_credit_control(events=["confirm"])
        res = super(
            AccountMove, self.with_context(skip_check_credit_control=True)
        ).action_post()
        return res

    def _check_credit_control(self, events=None):
        self.ensure_one()

        if not events:
            events = ["confirm_edit", "confirm"]

        if self._context.get("skip_check_credit_control", False):
            return

        if self._context.get("website_order_tx", False):
            return

        if self.skip_credit_control_rules:
            return

        if "website_id" in self._fields and self.website_id:
            return

        partner_id = self.partner_id.sudo().commercial_partner_id

        policy_id = partner_id.credit_control_policy_id

        if not policy_id:
            policy_id = (
                self.env["credit.control.policy"]
                .sudo()
                .search([("default", "=", True)], limit=1)
            )

        if policy_id:
            return policy_id.check_rules(events, partner_id, self)
