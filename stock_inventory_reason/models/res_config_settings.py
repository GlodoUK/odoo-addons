from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    use_fixed_inventory_adjustment_reason = fields.Boolean(
        related="company_id.use_fixed_inventory_adjustment_reason",
        readonly=False,
    )
    require_inventory_adjustment_reason = fields.Boolean(
        related="company_id.require_inventory_adjustment_reason",
        readonly=False,
    )
