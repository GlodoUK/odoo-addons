from odoo import api, fields, models
from odoo.exceptions import UserError


class StockInventoryAdjustmentName(models.TransientModel):
    _inherit = "stock.inventory.adjustment.name"

    reason_id = fields.Many2one(
        "stock.inventory.adjustment.reason",
        domain="[('company_id', 'in', [False, company_id])]",
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, readonly=True
    )
    use_fixed_reason = fields.Boolean(
        compute="_compute_company_settings", compute_sudo=True
    )
    require_reason = fields.Boolean(
        compute="_compute_company_settings", compute_sudo=True
    )

    @api.depends("company_id")
    def _compute_company_settings(self):
        for wizard in self:
            company = wizard.company_id or self.env.company
            wizard.use_fixed_reason = company.use_fixed_inventory_adjustment_reason
            wizard.require_reason = company.require_inventory_adjustment_reason

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.company.require_inventory_adjustment_reason:
            # Don't let the stock default satisfy the requirement
            res["inventory_adjustment_name"] = False
        return res

    @api.onchange("reason_id")
    def _onchange_reason_id(self):
        if self.reason_id:
            self.inventory_adjustment_name = self.reason_id.name

    def action_apply(self):
        self.ensure_one()
        if self.use_fixed_reason and self.reason_id:
            self.inventory_adjustment_name = self.reason_id.name
        if self.require_reason:
            if self.use_fixed_reason and not self.reason_id:
                raise UserError(self.env._("Please select an inventory reason."))
            if not (self.inventory_adjustment_name or "").strip():
                raise UserError(self.env._("Please enter an inventory reason."))
        elif not self.inventory_adjustment_name:
            self.inventory_adjustment_name = "Physical Inventory"
        return super().action_apply()
