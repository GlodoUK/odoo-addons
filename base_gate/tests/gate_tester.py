from odoo import fields, models


class GateTestModel(models.Model):
    """Throwaway model (loaded only during tests) to exercise gate.mixin end-to-end
    against a model that is NOT sale.order — proving the framework is model-agnostic."""

    _name = "gate.test.model"
    _description = "Gate Test Model"
    _inherit = ["gate.mixin"]

    name = fields.Char()
    amount = fields.Float()
    user_id = fields.Many2one("res.users")
    confirmed = fields.Boolean()

    def action_confirm(self):
        """Guarded action. Gate first; only the records that pass are confirmed."""
        proceed = self._check_gates(["manual"])
        proceed.with_context(skip_gates=True).write({"confirmed": True})
        return proceed

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("skip_gates"):
            # dynamic re-evaluation on edit — never blocks the edit itself
            self._sync_gates(["manual"])
        return res
