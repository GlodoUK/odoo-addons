from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    channel_id = fields.Many2one(
        "helpdesk.channel", default=lambda s: s._get_default_channel_id()
    )

    def _get_default_channel_id(self):
        return self.team_id.default_channel_id

    @api.onchange("team_id")
    def _onchange_team_id_channel(self):
        self.channel_id = self._get_default_channel_id()
