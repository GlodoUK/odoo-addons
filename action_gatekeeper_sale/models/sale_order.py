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

    def action_quotation_send(self):
        # Check gatekeeper rules before sending the quotation.
        for record in self:
            record._sync_gatekeeper_lines()
            record._check_gatekeeper_rules("action_quotation_send")
        return super().action_quotation_send()

    def action_cancel(self):
        for record in self:
            record._reset_gatekeeper_rules()
            record._sync_gatekeeper_lines()
            record._check_gatekeeper_rules("action_cancel")
        return super().action_cancel()

    def action_draft(self):
        for record in self:
            record._reset_gatekeeper_rules()
            record._sync_gatekeeper_lines()
            record._check_gatekeeper_rules("action_draft")
        return super().action_draft()
