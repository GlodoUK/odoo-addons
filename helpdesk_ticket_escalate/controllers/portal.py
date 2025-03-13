from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    @http.route(
        ["/helpdesk/ticket/<int:ticket_id>/escalate"],
        type="http",
        auth="user",
        website=True,
        methods=["GET"],
    )
    def helpdesk_ticket_toggle_is_escalated(self, ticket_id, **kwargs):
        try:
            helpdesk_ticket = self._document_check_access(
                "helpdesk.ticket", ticket_id, None
            ).with_user(request.env.user)
        except (AccessError, MissingError):
            return request.redirect("/my/tickets")

        helpdesk_ticket = helpdesk_ticket.with_user(request.env.user).sudo()

        helpdesk_ticket.action_toggle_escalated()

        helpdesk_ticket.message_subscribe(
            helpdesk_ticket.team_id.escalate_message_partner_ids.ids
        )  # noqa

        return request.redirect(f"/helpdesk/ticket/{ticket_id}")
