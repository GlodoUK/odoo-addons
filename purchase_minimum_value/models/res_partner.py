from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_minimum_purchase_order_action = fields.Selection(
        [
            ("none", "Default / None"),
            ("block", "Block"),
        ],
        company_dependent=True,
        default="none",
        string="Min. Value Action",
    )

    property_minimum_purchase_order_currency_id = fields.Many2one(
        "res.currency",
        company_dependent=True,
        string="Currency",
    )

    # Cannot use fields.Monetary here as
    # company_dependent=True does not accept it
    property_minimum_purchase_order_value = fields.Float(
        company_dependent=True,
        string="Value",
    )
