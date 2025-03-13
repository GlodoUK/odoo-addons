from odoo import _, http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class EscalateCustomerPortal(CustomerPortal):
    @http.route(
        [
            "/my/ticket/escalate/<int:ticket_id>",
            "/my/ticket/escalate/<int:ticket_id>/<access_token>",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def escalate_ticket(self, ticket_id, access_token, **kw):
        try:
            ticket_sudo = self._document_check_access(
                "helpdesk.ticket", ticket_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        if not ticket_sudo.can_be_escalated:
            raise UserError(_("This ticket cannot be escalated any further"))

        ticket_sudo.with_user(request.env.user).sudo()._action_escalate(
            msg=_("Ticket escalated by the customer")
        )

        return request.redirect(f"/my/ticket/{ticket_id}/{access_token or ''}")
