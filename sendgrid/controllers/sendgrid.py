from odoo import http, api, SUPERUSER_ID, registry
import contextlib


@contextlib.contextmanager
def _with_environment(db):
    with api.Environment.manage():
        with registry(db).cursor() as new_cr:
            env = api.Environment(new_cr, SUPERUSER_ID, {})
            yield env


class Sendgrid(http.Controller):
    def _validate_sendgrid_webhook(self):
        return True

    @http.route('/sendgrid/inbound/<string:db>', auth='none', type='http', csrf=False)
    def sendgrid_inbound(self, db, **kwargs):
        if not self._validate_sendgrid_webhook():
            response = http.request.make_response("Could not validate webhook")
            response.status_code = 200  # prevent sendgrid fom retrying.
            return response

        with _with_environment(db) as env:
            mime = kwargs.get("email", "")
            if not mime:
                return 'OK'

            try:
                with env.cr.savepoint():
                    env['mail.thread'].message_process(False, mime)
            except ValueError as e:
                response = http.request.make_response(str(e))
                response.status_code = 200  # prevent sendgrid fom retrying.
                return response
