from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + [
            "credit_control_policy_id",
        ]

    credit_control_policy_id = fields.Many2one(
        "credit.control.policy",
        required=False,
        index=True,
        groups="account.group_account_invoice,account.group_account_readonly",
    )
