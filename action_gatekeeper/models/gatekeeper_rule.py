import base64
import re

from odoo import fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import safe_eval as safe_eval_module
from odoo.tools.safe_eval import safe_eval, wrap_module

_BASE64 = wrap_module(base64, ["b64encode", "b64decode"])
_RE = wrap_module(
    re, ["match", "search", "sub", "subn", "split", "findall", "finditer", "compile"]
)


class GatekeeperRule(models.Model):
    _name = "gatekeeper.rule"
    _description = "Gatekeeper Rule"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    name = fields.Char(required=True)
    target_model = fields.Selection([])

    trigger = fields.Many2one(
        "gatekeeper.trigger",
        required=True,
    )

    rule = fields.Selection(
        selection=[
            ("always", "Always"),
            ("record_domain", "Record Matches Custom Filter"),
            ("code", "Python Code"),
        ],
        required=True,
        string="Condition",
    )

    record_domain = fields.Char(
        default="[]",
    )

    action = fields.Selection(
        [("block", "Block"), ("hold", "Hold")],
        required=True,
        default="block",
        help=(
            "Action to take when this rule is triggered."
            "\nBlock prevents the action from completing until bypassed."
            "\nHold allows the action to complete but flags the record as on hold."
        ),
    )

    code = fields.Text(
        help="Set variable trigger_rule = True to trigger the rule (False if not set)",
        default="""# Available variables:
# rule_id: Current gatekeeper rule being evaluated
# record_id: Current record being evaluated
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

trigger_rule = False
""",
    )

    release_users = fields.Many2many(
        "res.users",
        help="Users allowed to release/bypass this rule.",
    )

    release_groups = fields.Many2many(
        "res.groups",
        help="Members of these groups are allowed to release/bypass this rule.",
    )

    def _check_rule(self, record) -> bool:
        # Return True if the rule triggers, False otherwise.
        self.ensure_one()
        if self._check_is_released(record):
            return False
        if self.rule == "always":
            return True
        elif self.rule == "never":
            return False
        elif self.rule == "record_domain":
            domain = safe_eval(self.record_domain)
            result = record.filtered_domain(domain)
            return bool(result)
        elif self.rule == "code":
            eval_context = {
                "rule_id": self,
                "record_id": record,
                "env": self.env,
                "time": safe_eval_module.time,
                "datetime": safe_eval_module.datetime,
                "relativedelta": safe_eval_module.dateutil.relativedelta,
                "rrule": safe_eval_module.dateutil.rrule,
                "base64": _BASE64,
                "Warning": UserError,
                "ValueError": ValueError,
                "ValidationError": ValidationError,
                "re": _RE,
                "next": next,
                "iter": iter,
            }
            safe_eval(self.code, eval_context, mode="exec")
            return eval_context.get("trigger_rule", False)
        else:
            return True

    def _check_can_release(self, user) -> bool:
        self.ensure_one()
        if user in self.release_users:
            return True
        if self.release_groups and user.all_group_ids & self.release_groups:
            return True
        return False

    def _check_is_released(self, record):
        self.ensure_one()

        for rule in record.gatekeeper_rule_lines:
            if rule.rule_id == self:
                if rule.is_released:
                    return True
                else:
                    return False
        return False
