from odoo import _, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    forwarding_enabled = fields.Boolean(
        default=False,
        string="Forward Emails",
    )
    forwarding_partner_id = fields.Many2one(
        "res.partner",
        string="Forwarding Partner",
    )
    forwarding_rule_ids = fields.One2many("res.partner.forwarding.rule", "partner_id")

    def _forwarding_find_matching_rule(self, model_name):
        self.ensure_one()
        if not self.forwarding_enabled:
            return self.env["res.partner.forwarding.rule"]

        return

    def _forwarding_to_partner(self, model_name):
        # recursively find where to forward to
        self.ensure_one()

        if not self.forwarding_enabled or not self.forwarding_rule_ids:
            return self

        matching_rule_id = self.forwarding_rule_ids._match_rule(model_name)
        if not matching_rule_id.forwarding_to_partner_id:
            return self

        return matching_rule_id.forwarding_to_partner_id._forwarding_to_partner(
            model_name
        )

    def action_open_forwarding_rules(self):
        self.ensure_one()

        return {
            "res_model": "res.partner.forwarding.rule",
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "domain": [("partner_id", "=", self.id)],
            "name": _("Email Forwarding Rules"),
            "context": {
                "default_partner_id": self.id,
            },
            "target": "new",
        }
