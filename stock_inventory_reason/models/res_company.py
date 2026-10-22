from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    use_fixed_inventory_adjustment_reason = fields.Boolean(
        string="Use fixed inventory adjustment reasons",
    )
    require_inventory_adjustment_reason = fields.Boolean(
        string="Require inventory adjustment reason",
    )
