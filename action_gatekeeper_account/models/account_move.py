from odoo import models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "gatekeeper.mixin"]

    def action_post(self):
        for record in self:
            record._sync_gatekeeper_lines()
            record._check_gatekeeper_rules("action_post")
        return super().action_post()

    def button_cancel(self):
        for record in self:
            record._reset_gatekeeper_rules()
            record._sync_gatekeeper_lines()
            record._check_gatekeeper_rules("button_cancel")
        return super().button_cancel()

    def button_draft(self):
        for record in self:
            record._reset_gatekeeper_rules()
            record._sync_gatekeeper_lines()
            record._check_gatekeeper_rules("button_draft")
        return super().button_draft()
