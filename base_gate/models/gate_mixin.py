from odoo import fields, models
from odoo.exceptions import UserError


class GateMixin(models.AbstractModel):
    """Make a model gate-able. Inherit alongside the model:

        class SaleOrder(models.Model):
            _name = "sale.order"
            _inherit = ["sale.order", "gate.mixin"]

    then call ``self._check_gates([...])`` from the guarded action, and override
    ``_gate_triggers`` / ``_requester_users`` as needed.

    Deliberately edit-safe: gate state lives on gate.hold records found by search, never as
    fields that lock this record, and this mixin never touches the host's ``state``.
    """

    _name = "gate.mixin"
    _description = "Gate Mixin"

    gate_hold_ids = fields.One2many(
        "gate.hold",
        "res_id",
        string="Gate Holds",
        domain=lambda self: [("res_model", "=", self._name)],
        auto_join=True,
    )
    gate_state = fields.Selection(
        [
            ("open", "Open"),  # no holds raised
            ("blocked", "Blocked"),  # an uncleared, blocking hold exists
            ("flagged", "Flagged"),  # only non-blocking holds remain uncleared
            ("cleared", "Cleared"),  # holds exist, all cleared
        ],
        string="Gate Status",
        compute="_compute_gate_state",
    )

    def _compute_gate_state(self):
        for record in self:
            holds = record.gate_hold_ids
            uncleared = holds.filtered(lambda h: h.state != "cleared")
            if not holds:
                record.gate_state = "open"
            elif not uncleared:
                record.gate_state = "cleared"
            elif any(h._action_blocks() for h in uncleared):
                record.gate_state = "blocked"
            else:
                record.gate_state = "flagged"

    # -- hooks for consumers to override --

    def _gate_triggers(self):
        """Triggers this model fires (informational; consumers pass triggers explicitly)."""
        return []

    def _requester_users(self):
        """Users considered the requester — barred from self-clearing unless allow_self."""
        self.ensure_one()
        users = self.env["res.users"]
        for fname in ("user_id", "create_uid"):
            field = self._fields.get(fname)
            if field and field.comodel_name == "res.users":
                users |= self[fname]
        return users

    # -- engine --

    def _gate_rules(self, triggers):
        """Rules currently in scope AND tripping for this record, in tier order."""
        self.ensure_one()
        rules = self.env["gate.rule"].search(
            [
                ("model_name", "=", self._name),
                ("trigger", "in", triggers),
            ],
            order="sequence, id",
        )
        return rules.filtered(lambda r: r._matches(self) and r._evaluate(self))

    def _sync_gates(self, triggers):
        """Materialise/resolve holds to reflect currently-tripping rules, then recompute
        the waterfall. Idempotent; safe to call on every write. Returns this record's holds."""
        Hold = self.env["gate.hold"].sudo()
        result = self.env["gate.hold"]
        for record in self:
            matching = record._gate_rules(triggers)
            existing = record.gate_hold_ids.sudo()
            # drop holds whose rule no longer trips — but only within the triggers being
            # synced, so re-gating on one trigger never wipes holds from another.
            stale = existing.filtered(
                lambda h: h.rule_id.trigger in triggers
                and h.rule_id not in matching
                and h.state != "cleared"
            )
            stale.unlink()
            missing = matching - existing.mapped("rule_id")
            for rule in missing:
                Hold.create(
                    {
                        "rule_id": rule.id,
                        "res_model": record._name,
                        "res_id": record.id,
                    }
                )
            record._recompute_hold_states()
            result |= record.gate_hold_ids
        return result

    def _recompute_hold_states(self):
        """Set each hold's waterfall state: the lowest uncleared tier is `pending`, higher
        tiers `waiting`, cleared tiers `cleared`.

        Deliberately only sets state — `_action_apply` is fired by the consumer after the
        guarded action runs (so non-blocking consequences see downstream records), and
        `_action_release` is fired on clearance."""
        for record in self:
            holds = record.gate_hold_ids.sudo()
            uncleared = holds.filtered(lambda h: not h._is_cleared())
            active = min(uncleared.mapped("tier"), default=None)
            for hold in holds:
                if hold._is_cleared():
                    state = "cleared"
                elif hold.tier == active:
                    state = "pending"
                else:
                    state = "waiting"
                if hold.state != state:
                    hold.state = state

    def _check_gates(self, triggers):
        """Enforcement entrypoint. Returns the subset of `self` that may proceed.

        Blocking hold + no clearer group -> raise (absolute stop).
        Blocking hold + clearer group    -> hold back + notify (routable; caller must not proceed).
        Non-blocking holds only          -> proceed (caller applies effects after super()).
        """
        proceed = self.browse()
        for record in self:
            raised = record._sync_gates(triggers).filtered(lambda h: not h._is_cleared())
            blocking = raised.filtered(lambda h: h._action_blocks())
            absolute = blocking.filtered(lambda h: not h.rule_id.dismiss_group_id)
            if absolute:
                raise UserError(
                    self.env._(
                        "Blocked by gate: %s",
                        ", ".join(absolute.mapped("rule_id.name")),
                    )
                )
            if blocking:
                record._notify_gated(blocking)
            else:
                proceed |= record
        return proceed

    def _notify_gated(self, holds):
        """Hook: tell the clearers a record is waiting. Default no-op; override to post
        activities/messages to `holds.rule_id.dismiss_group_id`."""
        return
