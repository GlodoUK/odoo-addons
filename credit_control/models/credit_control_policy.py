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
    action = fields.Selection(
        [("block", "Block"), ("hold", "Hold")], default="block", required=True
    )

    rule_count = fields.Integer(compute="_compute_rule_count", store=True)

    partner_ids = fields.One2many(
        "res.partner",
        "credit_control_policy_id",
        readonly=True,
    )

    partner_count = fields.Integer(compute="_compute_partner_count", store=True)
    default = fields.Boolean(default=False)

    @api.constrains("default")
    def _check_default(self):
        if self.default:
            if self.search_count([("default", "=", True)]) > 1:
                raise UserError(
                    _("You can only have one default credit control policy.")
                )

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
        elif res and self.action == "hold":
            if not sale_id.credit_control_hold:
                self.post_todo_task(sale_id, res)
        return res

    def post_todo_task(self, sale_id, res):
        self.ensure_one()

        task_vals = {
            "note": _("Credit Control Policy: %s") % (",".join(res.mapped("name"))),
            "user_id": self.env.user.id,
            "date_deadline": fields.Date.today(),
            "state": "open",
            "activity_type_id": self.env.ref("credit_control.activity_sale_hold").id,
            "res_id": sale_id.id,
            "res_model_id": self.env.ref("sale.model_sale_order").id,
        }
        sale_id.credit_control_hold = self.env["mail.activity"].create(task_vals)

    def action_open_partners(self):
        self.ensure_one()
        action = self.env.ref("base.action_partner_form").read([])[0]
        if action:
            action["domain"] = [
                ("id", "in", self.partner_ids.ids),
            ]
            return action
