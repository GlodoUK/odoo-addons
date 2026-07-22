from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class CreditControlPolicy(models.Model):
    _name = "credit.control.policy"
    _description = "Credit Control Policy"

    active = fields.Boolean(
        default=True,
    )

    name = fields.Char(
        required=True,
    )

    default = fields.Boolean(
        default=False,
    )

    partner_ids = fields.One2many(
        "res.partner",
        "credit_control_policy_id",
        readonly=True,
    )

    partner_count = fields.Integer(
        compute="_compute_partner_count",
        store=True,
    )

    rule_ids = fields.One2many(
        "credit.control.rule",
        "policy_id",
        context={"active_test": False},
    )

    rule_count = fields.Integer(
        compute="_compute_rule_count",
        store=True,
    )

    action = fields.Selection(
        [("block", "Block"), ("hold", "Hold Sale")],
        default="block",
        required=True,
        help=(
            "Action to take when a rule is triggered."
            "\nNote: Hold only applies to records with a credit_control_hold field."
        ),
    )

    action_bypass_users = fields.Many2many("res.users", string="Bypass Users")
    action_bypass_groups = fields.Many2many("res.groups", string="Bypass Groups")

    # ruff: noqa: E501
    @api.constrains("default")
    def _check_default(self):
        if self.search_count([("default", "=", True)]) > 1:
            raise ValidationError(
                self.env._("There should be only one credit control policy")
            )

    @api.depends("partner_ids")
    def _compute_partner_count(self):
        for policy in self:
            policy.partner_count = len(policy.partner_ids)

    @api.depends("rule_ids")
    def _compute_rule_count(self):
        for policy in self:
            policy.rule_count = len(policy.rule_ids)

    def check_rules(self, events, partner_id, record):
        self.ensure_one()

        res = self.env["credit.control.rule"]

        for rule_id in self.rule_ids.filtered(lambda r: r.active and r.event in events):
            result = rule_id.check_rule(partner_id, record)

            if result:
                res |= rule_id

        if res and self.action == "block":
            raise UserError(
                self.env._(
                    "Blocked by Credit Control Policy\n%s",
                    ",".join(res.mapped("display_name")),
                )
            )
        elif (
            res and self.action == "hold" and record._fields.get("credit_control_hold")
        ):
            if not record.credit_control_hold:
                self.post_todo_task(record, res)

        return res

    def post_todo_task(self, record, res):
        self.ensure_one()

        activity_vals = {
            "note": self.env._(
                "Credit Control Policy: %s", ",".join(res.mapped("display_name"))
            ),
            "user_id": self.env.user.id,
            "date_deadline": fields.Date.today(),
            "state": "open",
            "activity_type_id": self.env.ref("credit_control.activity_sale_hold").id,
            "res_id": record.id,
            "res_model_id": self.env.ref(
                f"{record._module}.model_{record._name.replace('.', '_')}"
            ).id,
        }

        record.credit_control_hold = self.env["mail.activity"].create(activity_vals)

    def action_open_partners(self):
        self.ensure_one()

        action = self.env.ref("base.action_partner_form").read([])[0]

        if action:
            action["domain"] = [("id", "in", self.partner_ids.ids)]

        return action
