from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    @http.route(
        [
            "/helpdesk/ticket/escalate/<int:ticket_id>",
            "/helpdesk/ticket/escalate/<int:ticket_id>/<access_token>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def ticket_escalate(self, ticket_id, access_token=None, **kwargs):
        try:
            ticket_sudo = self._document_check_access(
                "helpdesk.ticket", ticket_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my/tickets")

        # Ensure tracking=True message is posted by request.env.user
        ticket_sudo = ticket_sudo.with_user(request.env.user).sudo()

        ticket_sudo.action_toggle_escalated()

        ticket_sudo.message_subscribe(
            ticket_sudo.team_id.escalate_message_partner_ids.ids
        )

        return request.redirect(f"/my/ticket/{ticket_id}/{access_token or ''}")
