import base64
import datetime
import re
import time

from dateutil import relativedelta, rrule

from odoo import _, addons, api, exceptions, fields, models
from odoo.tools import float_compare
from odoo.tools.safe_eval import safe_eval


class CreditControlRule(models.Model):
    _name = "credit.control.rule"
    _description = "Hold Policy Rules"
    _order = "sequence asc"

    def name_get(self):
        res = []

        for record in self:
            res.append(
                (
                    record.id,
                    "{} > {}/{}".format(
                        record.policy_id.name,
                        record.classification_id.name,
                        record.name,
                    ),
                )
            )

        return res

    classification_id = fields.Many2one(
        "credit.control.classification",
        required=True,
    )

    policy_id = fields.Many2one(
        "credit.control.policy",
        index=True,
        required=True,
        ondelete="cascade",
    )

    name = fields.Char(
        required=False,
        string="Description",
        help="Optional descriptive message",
    )

    @api.onchange("rule")
    def _onchange_rule(self):
        rule_strings = dict(self._fields["rule"].selection).values()

        if self.name and self.name not in rule_strings:
            return

        self.name = dict(self._fields["rule"].selection).get(self.rule)

    sequence = fields.Integer(default=0)

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
        string="Hold Condition",
        required=True,
    )

    sale_domain = fields.Char(
        string="Sale Filter",
        default="[]",
    )

    partner_domain = fields.Char(string="Partner Filter", default="[]")

    event = fields.Selection(
        [
            ("confirm", "On confirmation"),
            ("confirm_edit", "On confirm, and edit after confirm"),
            ("edit", "On edit after confirm"),
        ],
        default="confirm",
        required=True,
    )

    active = fields.Boolean(default=True)

    code = fields.Text(
        help="""Set variable hold = True if you want the sale to be placed on hold.""",
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

    def check_rule(self, partner_id, sale_id):
        # Returns tuple, true/false and reason
        self.ensure_one()
        method = getattr(self, "_check_rule_%s" % (self.rule))
        return method(partner_id, sale_id)

    def _check_rule_always(self, _partner_id, _sale_id):
        return True

    def _check_rule_never(self, _partner_id, _sale_id):
        return False

    def _check_rule_sale_domain(self, partner_id, sale_id):
        if self.sale_domain:
            domain = safe_eval(self.sale_domain) + [("id", "=", sale_id.id)]
            result = self.env["sale.order"].search_count(domain) > 0
            if result:
                return True

        return False

    def _check_rule_partner_domain(self, partner_id, _sale_id):
        if self.partner_domain:
            domain = safe_eval(self.partner_domain) + [("id", "=", partner_id.id)]
            result = self.env["res.partner"].search_count(domain) > 0

            if result:
                return True

        return False

    def _check_rule_over_limit(self, partner_id, sale_id):
        if partner_id.credit_control_used > partner_id.credit_control_limit:
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
                partner_id.credit_control_used + sale_amount,
                partner_id.credit_control_limit,
                precision_rounding=partner_id.currency_id.rounding,
            )
            > 0
        ):
            return True

        return False

    def _check_rule_proforma(self, partner_id, sale_id):
        if sale_id.payment_term_id:
            proforma_count = self.env["account.payment.term.line"].search_count(
                [
                    ("payment_id", "=", sale_id.payment_term_id.id),
                    ("value", "=", "balance"),
                    ("option", "=", "day_after_invoice_date"),
                    ("days", "=", 0),
                ]
            )

            if proforma_count > 0:
                return True

        return False

    def _check_rule_code(self, partner_id, sale_id):
        eval_context = {
            "rule_id": self,
            "sale_id": sale_id,
            "partner_id": partner_id,
            "env": self.env,
            "time": time,
            "datetime": datetime,
            "relativedelta": relativedelta,
            "rrule": rrule,
            "base64": base64,
            "Warning": exceptions.Warning,
            "_": _,
            "ValueError": ValueError,
            "re": re,
            "next": next,
            "iter": iter,
            "fields": fields,
            "addons": addons,
            "wdb": __import__("wdb"),
        }

        safe_eval(
            self.code, eval_context, mode="exec", nocopy=True
        )  # nocopy allows to return 'hold'

        return eval_context.get("hold", False)
