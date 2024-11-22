import requests
import email

from odoo import models, api


import logging
_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def mailgun_fetch_message(self, message_url):
        api_key = self.env['ir.config_parameter'].sudo().get_param('mailgun.apikey')
        res = requests.get(message_url, headers={'Accept': 'message/rfc2822'}, auth=('api', api_key), verify=False)

        res_dict = res.json()

        # Inject the original RCPT TO into the email mime before passing it
        # upstream.
        #
        # We have to do this in 12.0 because message_route does not always use
        # the passed message_dict, and instead re-parses the original message.
        #
        # 13.0 does not have this issue and we can deal with this differently.
        #
        # This will break DKIM signing (in some circumstances), but Odoo
        # currently does not care about DKIM, SPF, etc. at present.
        #
        # This is useful in the following circumstances;
        # 1. The RCPT TO and mime To do not match. They do not have to.
        # 2. Different domains and forwarding
        #    - i.e. it's been forwarded from somewhere like o365 which does not
        #    set theDelivered-To header

        msg = email.message_from_string(res_dict.get('body-mime', ''))

        if res_dict.get('recipients'):
            del msg['Delivered-To']
            msg['To'] = res_dict.get('recipients', '')
            msg['Delivered-To'] = res_dict.get('recipients', '')

        body_mime = msg.as_string()

        self.message_process(False, body_mime)
