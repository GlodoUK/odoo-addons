import hashlib
import hmac

from odoo import http
from odoo.http import request


class MailMailgun(http.Controller):
    @http.route("/mailgun/notify", auth="public", type="http", csrf=False)
    def mailgun_notify(self, **kw):
        if not self._mailgun_verify(
            kw.get("token"), kw.get("timestamp"), kw.get("signature")
        ):
            response = http.request.make_response("Invalid signature")
            response.status_code = 406  # prevent mailgun from retrying.
            return response

        # mailgun notification in json format
        message_url = kw.get("message-url")

        request.env["mail.thread"].sudo().mailgun_fetch_message(message_url)
        return "Ok"

    def _mailgun_verify(self, token, timestamp, signature):
        if not signature:
            return False

        icp = request.env["ir.config_parameter"].sudo()
        api_key = icp.get_param("mailgun.webhookkey")

        if not api_key:
            return False

        hmac_digest = hmac.new(
            key=bytes(api_key, "utf-8"),
            msg="{}{}".format(timestamp, token).encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, hmac_digest)
