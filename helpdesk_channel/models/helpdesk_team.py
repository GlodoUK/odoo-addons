from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    default_channel_id = fields.Many2one(
        "helpdesk.channel",
    )
