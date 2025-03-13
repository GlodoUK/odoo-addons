from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    rule_ids = fields.One2many("helpdesk.rule", "team_id")
    rule_count = fields.Integer(compute="_compute_rule_count")

    def _compute_rule_count(self):
        for record in self:
            record.rule_count = len(record.rule_ids)

    def action_view_rules(self):
        self.ensure_one()
        action = self.env.ref("helpdesk_rules.helpdesk_rule_action").read()[0]
        action["domain"] = [("team_id", "=", self.id)]
        action["context"] = {"default_team_id": self.id}
        return action
