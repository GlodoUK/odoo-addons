from odoo import api, fields, models


class GateHold(models.Model):
    """A single rule currently raised on a single record.

    Discovered by the mixin via (res_model, res_id) search — deliberately NOT a field on
    the host record, so it never couples to or locks the host.
    """

    _name = "gate.hold"
    _description = "Gate Hold"
    _order = "res_model, res_id, tier, id"

    rule_id = fields.Many2one(
        "gate.rule",
        required=True,
        ondelete="cascade",
        index=True,
    )
    res_model = fields.Char(string="Document Model", required=True, index=True)
    res_id = fields.Integer(string="Document", required=True, index=True)
    tier = fields.Integer(
        related="rule_id.sequence",
        store=True,
        help="Waterfall position, copied from the rule's tier.",
    )
    clearance_ids = fields.One2many("gate.clearance", "hold_id", string="Clearances")
    clearance_count = fields.Integer(compute="_compute_clearance_count")
    state = fields.Selection(
        [
            ("waiting", "Waiting"),  # a lower tier is still uncleared
            ("pending", "Pending"),  # active tier, clearable now
            ("cleared", "Cleared"),
        ],
        default="pending",
        required=True,
        index=True,
    )

    @api.depends("clearance_ids")
    def _compute_clearance_count(self):
        for hold in self:
            hold.clearance_count = len(hold.clearance_ids)

    def record(self):
        """The host record this hold is raised on."""
        self.ensure_one()
        return self.env[self.res_model].browse(self.res_id)

    def _is_cleared(self):
        self.ensure_one()
        return len(self.clearance_ids) >= (self.rule_id.min_dismissals or 1)

    # -- pluggable action dispatch (see gate.rule.action) --

    def _action_blocks(self):
        """Does this raised hold PREVENT the guarded action from proceeding?"""
        self.ensure_one()
        handler = getattr(self, f"_action_{self.rule_id.action}_blocks", None)
        return handler() if handler else True  # default: block

    def _action_apply(self):
        """Side effects when the gate is raised (fired when its tier becomes active)."""
        for hold in self:
            handler = getattr(hold, f"_action_{hold.rule_id.action}_apply", None)
            if handler:
                handler()

    def _action_release(self):
        """Side effects when the hold becomes cleared."""
        for hold in self:
            handler = getattr(hold, f"_action_{hold.rule_id.action}_release", None)
            if handler:
                handler()

    # -- base action: block --

    def _action_block_blocks(self):
        return True
