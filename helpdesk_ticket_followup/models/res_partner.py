from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    snooze_till_date = fields.Date(
        help="User sets up date till which he does not want to"
        " receive followup emails."
    )
    is_send_followup_1st = fields.Boolean(
        string="Send first followup",
        help="User sets if he wants to receive first followup messageh.",
        default=True,
    )
    is_send_followup_2nd = fields.Boolean(
        string="Send second followup",
        help="User sets if he wants to receive second followup message.",
        default=True,
    )
