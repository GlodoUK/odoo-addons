import phonenumbers
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from odoo import api, models


class SmsApi(models.AbstractModel):
    _inherit = "sms.api"

    @api.model
    def _twilio_send_sms_batch(self, messages, raise_on_exception=False):
        """
        Send SMS using Twilio in batch mode

        :param messages: list of SMS to send, structured as dict [{
            'res_id':  integer: ID of sms.sms,
            'number':  string: E164 formatted phone number,
            'content': string: content to send
        }]

        :return: compatible with upstream _send_sms_batch: list of dict [{
            'res_id': integer: ID of sms.sms,
            'state':  string: 'insufficient_credit' or 'wrong_number_format' or 'success',
            'credit': integer: number of credits spent to send this SMS,
        }]
        """  # noqa: E501

        icp = self.env["ir.config_parameter"].sudo()

        account_sid = icp.get_param("twilio_sms.sid", default="")
        auth_token = icp.get_param("twilio_sms.token", default="")
        country_code = icp.get_param(
            "twilio_sms.default_country_code", default=self.env.company.country_id.code
        )
        send_as = icp.get_param("twilio_sms.from", default="")
        create_log = icp.get_param("twilio_sms.log", default=False)

        client = Client(account_sid, auth_token)
        res = []
        log_data = []

        for message in messages:
            res_id = message.get("res_id")
            number = message.get("number")
            content = message.get("content")

            try:
                parsed_number = phonenumbers.parse(number, country_code)
                e164_formatted_number = phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.E164
                )

                req = client.messages.create(
                    body=content, from_=send_as, to=e164_formatted_number
                )

                res.append(
                    {
                        "state": "success",
                        "res_id": res_id,
                        "credit": 0,
                    }
                )

                if create_log:
                    log_data.append(
                        {
                            "to": number,
                            "body": content,
                            "account_sid": account_sid,
                            "api_response": req,
                            "state": "done",
                        }
                    )
            except phonenumbers.NumberParseException as e:
                if raise_on_exception:
                    raise e
                res.append(
                    {
                        "state": "wrong_number_format",
                        "res_id": res_id,
                        "credit": 0,
                    }
                )
                if create_log:
                    log_data.append(
                        {
                            "to": number,
                            "body": content,
                            "account_sid": account_sid,
                            "api_response": e._msg,
                            "state": "error",
                        }
                    )
            except TwilioRestException as e:
                if raise_on_exception:
                    raise e
                res.append(
                    {
                        "state": "server_error",
                        "res_id": res_id,
                        "credit": 0,
                    }
                )
                if create_log:
                    log_data.append(
                        {
                            "to": number,
                            "body": content,
                            "account_sid": account_sid,
                            "api_response": e.msg,
                            "state": "error",
                        }
                    )

        if log_data:
            self.env["twilio_sms.log"].sudo().create(log_data)

        return res

    @api.model
    def _send_sms(self, numbers, message):
        twilio_enabled = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("twilio_sms.enabled", default=False)
        )

        if not twilio_enabled:
            return super()._send_sms(numbers, message)

        # Transform this into the format that _twilio_send_sms_batch expects
        messages_dict = [
            {
                "res_id": False,
                "number": number,
                "content": message,
            }
            for number in numbers
        ]

        # Returns True or raises an exception in upstream implementation.
        # So we need to mimic this.
        self._twilio_send_sms_batch(messages_dict, raise_on_exception=True)
        return True

    @api.model
    def _send_sms_batch(self, messages):
        twilio_enabled = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("twilio_sms.enabled", default=False)
        )

        if not twilio_enabled:
            return super()._send_sms_batch(messages)

        return self._twilio_send_sms_batch(messages)
