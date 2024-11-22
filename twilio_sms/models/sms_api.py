from twilio.rest import Client

from odoo import api, models


class SmsApi(models.AbstractModel):
    _inherit = "sms.api"

    @api.model
    def _send_sms(self, numbers, message):
        twilio_enabled = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("twilio.twilio_enabled", default=False)
        )

        if not twilio_enabled:
            return super(SmsApi, self)._send_sms(numbers, message)

        account_sid = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("twilio.twilio_sid", default="")
        )
        auth_token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("twilio.twilio_token", default="")
        )

        client = Client(account_sid, auth_token)

        for number in numbers:
            client.messages.create(
                body=message,
                from_=self.env.user.company_id.name,
                to=number
            )

        return True
