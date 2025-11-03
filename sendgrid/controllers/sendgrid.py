from odoo import SUPERUSER_ID, api, http
from odoo.modules.registry import Registry


class Sendgrid(http.Controller):
    def _validate_sendgrid_webhook(self):
        return True

    @http.route("/sendgrid/inbound/<string:db>", auth="none", type="http", csrf=False)
    def sendgrid_inbound(self, db, **kwargs):
        if not self._validate_sendgrid_webhook():
            response = http.request.make_response("Could not validate webhook")
            response.status_code = 200  # prevent sendgrid fom retrying.
            return response

        with Registry(db).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            mime = kwargs.get("email", "")
            if not mime:
                return "OK"

            try:
                with env.cr.savepoint():
                    env["mail.thread"].message_process(None, mime)
            except ValueError as e:
                response = http.request.make_response(str(e))
                response.status_code = 200  # prevent sendgrid fom retrying.
                return response
