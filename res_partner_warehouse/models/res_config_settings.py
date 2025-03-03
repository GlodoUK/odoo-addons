from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_res_partner_warehouse_select_seller = fields.Boolean(
        "Affect Purchase Seller Selection",
        implied_group="res_partner_warehouse.group_select_seller",
    )
