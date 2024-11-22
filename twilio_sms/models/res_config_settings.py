from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    twilio_enabled = fields.Boolean()
    twilio_sid = fields.Char()
    twilio_token = fields.Char()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        twilio_enabled = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("twilio.twilio_enabled", default=False)
        )

        twilio_sid = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("twilio.twilio_sid", default="")
        )

        twilio_token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("twilio.twilio_token", default="")
        )

        res.update(
            {
                "twilio_enabled": twilio_enabled,
                "twilio_sid": twilio_sid,
                "twilio_token": twilio_token,
            }
        )

        return res

    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()

        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("twilio.twilio_enabled", self.twilio_enabled or False)
        icp.set_param("twilio.twilio_sid", self.twilio_sid or "")
        icp.set_param("twilio.twilio_token", self.twilio_token or "")

        return res
