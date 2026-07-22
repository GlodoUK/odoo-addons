from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

CODE_HELP = """\
Available variables (condition = 'Python code'):
  - env:        Odoo Environment
  - record:     the record being evaluated
  - rule:       this gate.rule
  - user:       the current user
Set `raise_gate = True` to trip the gate. Example:
  raise_gate = record.amount_total > 10000
"""


class GateRule(models.Model):
    _name = "gate.rule"
    _description = "Gate Rule"
    _order = "sequence, id"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(
        default=10,
        help="The tier. Rules clear in ascending tier order (waterfall); "
        "rules sharing a tier clear in parallel.",
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
    )
    model_name = fields.Char(
        related="model_id.model",
        string="Model Name",
        store=True,
        index=True,
    )
    trigger = fields.Selection(
        selection="_selection_trigger",
        required=True,
        help="Which guarded action this rule is evaluated on.",
    )
    record_domain = fields.Char(
        string="Applies to",
        default="[]",
        help="Applicability scope. The rule is only considered for records matching "
        "this domain. Leave empty to always apply.",
    )
    condition = fields.Selection(
        selection="_selection_condition",
        required=True,
        default="always",
        help="Within scope, the test that trips the gate.",
    )
    code = fields.Text(help=CODE_HELP)
    action = fields.Selection(
        selection="_selection_action",
        required=True,
        default="block",
        help="What happens when the gate trips. Extensible by other modules.",
    )
    dismiss_group_id = fields.Many2one(
        "res.groups",
        string="Cleared by",
        help="Members of this group may clear the gate. Empty = an absolute block "
        "that cannot be cleared (only an Officer can force it).",
    )
    allow_self = fields.Boolean(
        string="Allow self-clearance",
        default=False,
        help="If unset, the record's requester(s) cannot clear their own gate.",
    )
    min_dismissals = fields.Integer(
        string="Minimum clearances",
        default=1,
        help="How many distinct clearances are required (>1 for a multi-approver tier).",
    )

    @api.model
    def _selection_trigger(self):
        # Extended per host model via selection_add (e.g. sale_gate adds on_confirm/on_edit).
        return [("manual", "Manual")]

    @api.model
    def _selection_condition(self):
        return [
            ("always", "Always (in scope)"),
            ("never", "Never"),
            ("code", "Python code"),
        ]

    @api.model
    def _selection_action(self):
        # Extended per behaviour via selection_add (e.g. sale_gate_stock adds block_stock_hold).
        return [("block", "Block")]

    @api.constrains("min_dismissals")
    def _check_min_dismissals(self):
        for rule in self:
            if rule.min_dismissals < 1:
                raise ValidationError(
                    self.env._("Minimum clearances must be at least 1.")
                )

    def _matches(self, record):
        """Is this rule in scope for `record`? (applicability, not the trip test)"""
        self.ensure_one()
        domain = safe_eval(self.record_domain or "[]")
        if not domain:
            return True
        return bool(record.filtered_domain(domain))

    def _evaluate(self, record):
        """Does the gate trip for `record`? Assumes the rule is already in scope."""
        self.ensure_one()
        return bool(getattr(self, f"_condition_{self.condition}")(record))

    def _condition_always(self, record):
        return True

    def _condition_never(self, record):
        return False

    def _condition_code(self, record):
        eval_context = self._code_eval_context(record)
        safe_eval(self.code or "", eval_context, mode="exec", nocopy=True)
        return eval_context.get("raise_gate", False)

    def _code_eval_context(self, record):
        self.ensure_one()
        return {
            "env": self.env,
            "record": record,
            "rule": self,
            "user": self.env.user,
            "raise_gate": False,
        }
