from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CreditControlPolicy(models.Model):
    _name = "credit.control.policy"
    _description = "Hold Policies"

    active = fields.Boolean(default=True)
    name = fields.Char()

    rule_ids = fields.One2many(
        "credit.control.rule",
        "policy_id",
        string="Rules",
        context={"active_test": False},
    )
    action = fields.Selection([("block", "Block")], default="block", required=True)

    rule_count = fields.Integer(compute="_compute_rule_count", store=True)

    partner_ids = fields.One2many(
        "res.partner",
        "credit_control_policy_id",
        readonly=True,
    )

    partner_count = fields.Integer(compute="_compute_partner_count", store=True)

    @api.depends("rule_ids")
    def _compute_rule_count(self):
        for record in self:
            record.rule_count = len(record.rule_ids)

    @api.depends("partner_ids")
    def _compute_partner_count(self):
        for record in self:
            record.partner_count = len(record.partner_ids)

    def check_rules(self, events, partner_id, sale_id):
        self.ensure_one()
        res = self.env["credit.control.rule"]

        for rule_id in self.rule_ids.filtered(lambda r: r.active and r.event in events):
            result = rule_id.check_rule(partner_id, sale_id)

            if result:
                res |= rule_id

        if res and self.action == "block":
            raise UserError(
                _("Credit Control Policy: %s") % (",".join(res.mapped("name")))
            )

        return res

    def action_open_partners(self):
        self.ensure_one()
        action = self.env.ref("base.action_partner_form").read([])[0]
        if action:
            action["domain"] = [
                ("id", "in", self.partner_ids.ids),
            ]
            return action
