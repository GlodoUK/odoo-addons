from odoo import fields, models


class GatekeeperRule(models.Model):
    _inherit = "gatekeeper.rule"

    trigger = fields.Selection(
        selection_add=[
            ("action_confirm", "On Confirm Sale"),
        ],
        ondelete={"action_confirm": "cascade"},
    )
    target_model = fields.Selection(
        selection_add=[
            ("sale.order", "Sales Order"),
        ],
        ondelete={"sale.order": "cascade"},
    )
