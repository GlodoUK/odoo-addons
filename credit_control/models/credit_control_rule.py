from odoo import _, api, exceptions, fields, models
from odoo.tools import float_compare
from odoo.tools.safe_eval import pytz, safe_eval


class CreditControlRule(models.Model):
    _name = "credit.control.rule"
    _description = "Credit Control Rule"
    _order = "sequence asc"

    @api.depends("event", "rule", "policy_id.name", "active")
    def _compute_display_name(self):
        for rule in self:
            event_name = dict(self._fields["event"].selection).get(rule.event)
            rule_name = dict(self._fields["rule"].selection).get(rule.rule)
            rule_inactive = ""
            if not rule.active:
                rule_inactive = " (" + self.env._("Inactive") + ")"
            rule.display_name = (
                f"{rule.policy_id.name}: {event_name} > {rule_name}{rule_inactive}"
            )

    active = fields.Boolean(
        default=True,
    )

    sequence = fields.Integer(
        default=0,
    )

    partner_domain = fields.Char(
        default="[]",
    )

    sale_domain = fields.Char(
        default="[]",
    )

    policy_id = fields.Many2one(
        "credit.control.policy",
        index=True,
        ondelete="cascade",
        required=True,
    )

    event = fields.Selection(
        [
            ("confirm", "On confirmation"),
            ("confirm_edit", "On confirm, and edit after confirm"),
            ("edit", "On edit after confirm"),
        ],
        default="confirm",
        required=True,
    )

    rule = fields.Selection(
        selection=[
            ("always", "Always"),
            ("never", "Never"),
            ("over_limit", "Sale Over Limit"),
            ("proforma", "Proforma Terms on Sale"),
            ("sale_domain", "Sale Matches Custom Filter"),
            ("partner_domain", "Partner Matches Custom Filter"),
            ("code", "Python Code"),
        ],
        required=True,
        string="Hold Condition",
    )

    code = fields.Text(
        help="Set variable hold = True for the sale to be placed on hold",
        default="""# Available variables:
# rule_id: Current credit control policy rule being evaluated
# sale_id: Current sale.order
# partner_id: Current sale res.partner
# env: Odoo env
# time
# datetime
# relativedelta
# rrule
# base64
# Warning
# ValueError
# re
# next
# iter
""",
    )

    def _onchange_rule(self):
        self.ensure_one()

        rule_strings = dict(self._fields["rule"].selection).values()

        if self.name and self.name not in rule_strings:
            return

        self.name = dict(self._fields["rule"].selection).get(self.rule)

    def check_rule(self, partner_id, sale_id):
        # Returns tuple, True/False and reason
        self.ensure_one()
        method = getattr(self, f"_check_rule_{self.rule}")
        return method(partner_id, sale_id)

    @api.model
    def _check_rule_always(self, _partner_id, _sale_id):
        return True

    @api.model
    def _check_rule_never(self, _partner_id, _sale_id):
        return False

    def _check_rule_sale_domain(self, _partner_id, sale_id):
        self.ensure_one()

        if self.sale_domain:
            domain = safe_eval(self.sale_domain) + [("id", "=", sale_id.id)]
            result = self.env["sale.order"].search_count(domain) > 0
            if result:
                return True

        return False

    def _check_rule_partner_domain(self, partner_id, _sale_id):
        self.ensure_one()

        if self.partner_domain:
            domain = safe_eval(self.partner_domain) + [("id", "=", partner_id.id)]
            result = self.env["res.partner"].search_count(domain) > 0

            if result:
                return True

        return False

    def _check_rule_over_limit(self, partner_id, sale_id):
        if partner_id.credit > partner_id.credit_limit:
            return True

        sale_amount = sale_id.amount_total

        if sale_id.currency_id != partner_id.currency_id:
            sale_amount = sale_id.currency_id._convert(
                sale_amount,
                partner_id.currency_id,
                sale_id.company_id,
                fields.Date.today(),
            )

        if (
            sale_id.state == "draft"
            and float_compare(
                (partner_id.credit) + sale_amount,
                partner_id.credit_limit,
                precision_rounding=partner_id.currency_id.rounding,
            )
            > 0
        ):
            return True

        return False

    def _check_rule_proforma(self, _partner_id, sale_id):
        self.ensure_one()

        if sale_id.payment_term_id:
            proforma_count = self.env["account.payment.term.line"].search_count(
                [
                    ("payment_id", "=", sale_id.payment_term_id.id),
                    ("delay_type", "=", "day_after"),
                    ("nb_days", "=", 0),
                    ("value", "=", "percent"),
                ]
            )

            if proforma_count > 0:
                return True

        return False

    def _check_rule_code(self, partner_id, sale_id):
        self.ensure_one()

        eval_context = {
            "rule_id": self,
            "sale_id": sale_id,
            "partner_id": partner_id,
            "env": self.env,
            "Warning": exceptions.Warning,
            "_": _,
            "ValueError": ValueError,
            "next": next,
            "pytz": pytz,
        }

        safe_eval(
            self.code, eval_context, mode="exec", nocopy=True
        )  # nocopy allows to return 'hold'

        return eval_context.get("hold", False)
