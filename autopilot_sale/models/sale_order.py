from odoo import api, fields, models

# Shown first when an order has several bindings.
_STATE_PRIORITY = ["failed", "pending", "cancelled", "done"]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    autopilot_sale_binding_ids = fields.One2many(
        "autopilot_sale.order",
        "odoo_id",
        string="Sale EDI Bindings",
    )
    autopilot_sale_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("done", "Received"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        string="EDI Status",
        compute="_compute_autopilot_sale_state",
    )

    @api.depends("autopilot_sale_binding_ids.state")
    def _compute_autopilot_sale_state(self):
        for order in self:
            states = order.autopilot_sale_binding_ids.mapped("state")
            order.autopilot_sale_state = next(
                (state for state in _STATE_PRIORITY if state in states), False
            )

    def action_view_autopilot_sale_bindings(self):
        self.ensure_one()
        bindings = self.autopilot_sale_binding_ids
        action = {
            "type": "ir.actions.act_window",
            "name": self.env._("Sale EDI"),
            "res_model": "autopilot_sale.order",
            "view_mode": "list,form",
            "domain": [("odoo_id", "=", self.id)],
        }
        if len(bindings) == 1:
            action.update(view_mode="form", res_id=bindings.id)
        return action
