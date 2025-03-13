from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    glo_teams_webhook_url = fields.Char(string="Teams Webhook Url")

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env["ir.config_parameter"].sudo()
        res.update(
            glo_teams_webhook_url=params.get_param(
                "helpdesk_teams_message.glo_teams_webhook_url"
            )
        )
        return res

    def set_values(self):
        res = super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "helpdesk_teams_message.glo_teams_webhook_url", self.glo_teams_webhook_url
        )
        return res
