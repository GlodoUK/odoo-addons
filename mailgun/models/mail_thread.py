import logging

import requests

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def mailgun_fetch_message(self, message_url):
        api_key = self.env["ir.config_parameter"].sudo().get_param("mailgun.apikey")
        res = requests.get(
            message_url,
            headers={"Accept": "message/rfc2822"},
            auth=("api", api_key),
            verify=False,
        )

        res_dict = res.json()
        body_mime = res_dict.get("body-mime", "")
        self.with_context(
            mailgun_override_recipients=res_dict.get("recipients")
        ).message_process(False, body_mime)

    @api.model
    def message_parse(self, message, save_original=False):
        res = super(MailThread, self).message_parse(message, save_original)

        mailgun_override_recipients = self.env.context.get(
            "mailgun_override_recipients", ""
        )
        if mailgun_override_recipients:
            res["to"] = mailgun_override_recipients
            res["recipients"] = mailgun_override_recipients

        return res
