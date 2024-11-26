from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_minimum_purchase_order_currency_id = fields.Many2one(
        "res.currency",
        company_dependent=True,
    )
    # cannot use fields.Monetary here as company_dependent=True does not accept
    # it
    property_minimum_purchase_order_value = fields.Float(
        company_dependent=True,
        string="Purchase Order Minimum Value",
    )
    property_minimum_purchase_order_action = fields.Selection(
        [
            ("none", "Default / None"),
            ("block", "Block"),
        ],
        default="none",
        company_dependent=True,
        string="Minimum Purchase Value Enforcement",
    )
