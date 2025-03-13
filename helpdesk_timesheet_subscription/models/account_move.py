from odoo import models

INVOICE_INACTIVE_STATE = ["draft", "cancel"]
INVOICE_ACTIVE_STATE = ["posted"]


class AccountMove(models.Model):
    _inherit = "account.move"

    def add_substract_company_time(self, is_add):
        """Prepares update values to add or subtract from company time
        and triggers its update"""
        self.ensure_one()
        time_invoice_line_ids = self.invoice_line_ids.filtered(
            lambda il_id: not il_id.exclude_from_invoice_tab
            and il_id.product_id.is_time_replenisher
        )
        time_update_dict = {}
        for time_invoice_line_id in time_invoice_line_ids:
            time_update_dict[time_invoice_line_id.product_id.id] = (
                time_invoice_line_id.quantity if is_add else 0
            )
        self.partner_id.with_context(from_model_id=self).update_partners_time_balance(
            time_update_dict
        )

    def write(self, vals):
        """Adds support time to history or removes that time from history
        depending on state"""
        state_change = {}
        if "state" in vals and self:
            for obj in self:
                state_change[obj] = {}
                state_change[obj]["ex_state"] = obj.state
                state_change[obj]["new_state"] = vals.get("state")
        result = super().write(vals)
        for account_move, state_dict in state_change.items():
            if (
                state_dict["ex_state"] in INVOICE_INACTIVE_STATE
                and state_dict["new_state"] in INVOICE_ACTIVE_STATE
            ):
                account_move.add_substract_company_time(True)
            elif (
                state_dict["ex_state"] in INVOICE_ACTIVE_STATE
                and state_dict["new_state"] in INVOICE_INACTIVE_STATE
            ):
                account_move.add_substract_company_time(False)
        return result
