from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class GateClearance(models.Model):
    """One authorised sign-off against a hold. The audit trail; replaces credit_control's
    silent skip checkbox."""

    _name = "gate.clearance"
    _description = "Gate Clearance"
    _order = "date desc, id desc"

    _unique_hold_user = models.Constraint(
        "unique(hold_id, user_id)",
        "This user has already cleared this gate.",
    )

    hold_id = fields.Many2one(
        "gate.hold",
        required=True,
        ondelete="cascade",
        index=True,
    )
    rule_id = fields.Many2one(related="hold_id.rule_id", store=True)
    user_id = fields.Many2one(
        "res.users",
        string="Cleared by",
        required=True,
        default=lambda self: self.env.user,
    )
    date = fields.Datetime(default=fields.Datetime.now)
    note = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        clearances = super().create(vals_list)
        for clearance in clearances:
            clearance._check_authorised()
        clearances._after_clearance()
        return clearances

    def _is_officer(self, user):
        officer = self.env.ref(
            "base_gate.group_gate_officer", raise_if_not_found=False
        )
        return bool(officer) and user in officer.sudo().users

    def _check_authorised(self):
        self.ensure_one()
        rule = self.hold_id.rule_id
        user = self.user_id
        if self._is_officer(user):
            return  # officers may force-clear anything, any tier
        if rule.dismiss_group_id and user not in rule.dismiss_group_id.sudo().users:
            raise AccessError(
                self.env._("You are not authorised to clear this gate.")
            )
        if not rule.dismiss_group_id:
            raise UserError(
                self.env._(
                    "This gate is an absolute block and can only be force-cleared "
                    "by a Gate Officer."
                )
            )
        if self.hold_id.state == "waiting":
            raise UserError(
                self.env._("An earlier tier must be cleared before this one.")
            )
        if not rule.allow_self and user in self.hold_id.record()._requester_users():
            raise UserError(self.env._("You cannot clear your own gate."))

    def _after_clearance(self):
        """Recompute waterfall states and fire release hooks for holds that just cleared."""
        holds = self.mapped("hold_id")
        # A hold transitions to cleared exactly when its min-th clearance lands.
        newly_cleared = holds.filtered(
            lambda h: h.clearance_count == (h.rule_id.min_dismissals or 1)
        )
        for record in {(h.res_model, h.res_id) for h in holds}:
            self.env[record[0]].browse(record[1])._recompute_hold_states()
        newly_cleared._action_release()
