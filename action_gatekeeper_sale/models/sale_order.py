from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "gatekeeper.mixin"]

    def action_confirm(self):
        # Check gatekeeper rules before confirming the record.
        for record in self:
            record._sync_gatekeeper_lines()
            record._check_gatekeeper_rules("action_confirm")
        return super().action_confirm()

    def action_cancel(self):
        for record in self:
            record._reset_gatekeeper_rules()
        return super().action_cancel()
