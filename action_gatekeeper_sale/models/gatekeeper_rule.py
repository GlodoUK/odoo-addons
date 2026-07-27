from odoo import fields, models


class GatekeeperRule(models.Model):
    _inherit = "gatekeeper.rule"

    target_model = fields.Selection(
        selection_add=[
            ("sale.order", "Sales Order"),
        ],
        ondelete={"sale.order": "cascade"},
    )
