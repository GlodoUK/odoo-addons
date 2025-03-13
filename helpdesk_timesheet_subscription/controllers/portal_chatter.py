from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.mail import PortalChatter


class TimeLoggedPortalChatter(PortalChatter):
    @http.route("/mail/chatter_init", type="json", auth="public", website=True)
    def portal_chatter_init(
        self, res_model, res_id, domain=False, limit=False, **kwargs
    ):
        """Updates ticket with time logged if it is logged via wizard"""
        res = super().portal_chatter_init(res_model, res_id, domain, limit, **kwargs)
        if res_model == "helpdesk.ticket":
            for res_message in res.get("messages"):
                time_logged = (
                    request.env["mail.message"]
                    .sudo()
                    .browse(res_message.get("id"))
                    .mapped("glo_analytic_line_id.unit_amount")
                )
                res_message["time_logged"] = time_logged[0] if time_logged else False
        return res
