from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "gate.mixin"]

    def _gate_triggers(self):
        return ["on_confirm", "on_edit"]

    def _requester_users(self):
        self.ensure_one()
        return self.user_id | self.create_uid

    def action_confirm(self):
        if self.env.context.get("skip_gates"):
            return super().action_confirm()
        proceed = self._check_gates(["on_confirm"])
        result = super(
            SaleOrder, proceed.with_context(skip_gates=True)
        ).action_confirm()
        # Non-blocking consequences (e.g. place delivery on hold) fire after confirmation,
        # once their downstream targets exist.
        proceed.gate_hold_ids.filtered(
            lambda h: h.state != "cleared" and not h._action_blocks()
        )._action_apply()
        return result

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("skip_gates"):
            # Re-evaluate post-confirmation edit gates. Never blocks the edit itself —
            # it only materialises/resolves holds.
            confirmed = self.filtered(lambda o: o.state in ("sale", "done"))
            if confirmed:
                confirmed._sync_gates(["on_edit"])
        return res
