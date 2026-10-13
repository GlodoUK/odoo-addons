from odoo import api, fields, models

from .autopilot_purchase_order import STATES

# Most in need of attention first, for an order bound to several backends.
_STATE_PRIORITY = ["failed", "to_send", "pending", "cancelled", "done"]


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    autopilot_purchase_binding_ids = fields.One2many(
        "autopilot_purchase.order",
        "odoo_id",
        string="Purchase EDI Bindings",
    )
    autopilot_purchase_state = fields.Selection(
        STATES,
        string="EDI Status",
        compute="_compute_autopilot_purchase_state",
    )

    @api.depends("autopilot_purchase_binding_ids.state")
    def _compute_autopilot_purchase_state(self):
        for order in self:
            states = order.autopilot_purchase_binding_ids.mapped("state")
            order.autopilot_purchase_state = next(
                (state for state in _STATE_PRIORITY if state in states), False
            )

    # Not button_confirm. With two-step approval, a manager's Approve calls
    # this directly, and it is the only place a PO becomes confirmed.
    def button_approve(self, force=False):
        result = super().button_approve(force=force)
        self.env["autopilot_purchase.backend"]._bind(
            self.filtered(lambda order: order.state == "purchase")
        )
        return result

    def action_view_autopilot_purchase_bindings(self):
        self.ensure_one()
        bindings = self.autopilot_purchase_binding_ids
        action = {
            "type": "ir.actions.act_window",
            "name": self.env._("Purchase EDI"),
            "res_model": "autopilot_purchase.order",
            "view_mode": "list,form",
            "domain": [("odoo_id", "=", self.id)],
        }
        if len(bindings) == 1:
            action.update(view_mode="form", res_id=bindings.id)
        return action
