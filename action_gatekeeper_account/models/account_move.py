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

    def _get_gatekeeper_rules(self, event=None):
        # OVERWRITE the gatekeeper rules for this model to include move_type
        all_move_types = ["all"]
        if self.move_type in ["out_invoice", "out_refund"]:
            all_move_types.append("all_customer")
        elif self.move_type in ["in_invoice", "in_refund"]:
            all_move_types.append("all_vendor")
        elif self.move_type == "entry":
            all_move_types.append("entry")
        all_move_types.append(self.move_type)
        domain = [
            ("target_model", "=", self._name),
            ("target_move_type", "in", all_move_types),
        ]
        if event:
            domain.append(("trigger.action", "=", event))
        rules = self.env["gatekeeper.rule"].search(
            domain,
            order="sequence",
        )
        return rules
