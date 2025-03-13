from odoo import _, http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalReopen(CustomerPortal):
    @http.route(
        [
            "/my/ticket/reopen/<int:ticket_id>",
            "/my/ticket/reopen/<int:ticket_id>/<access_token>",
        ],
        type="http",
        auth="public",
        website=True,
    )
    def ticket_open(self, ticket_id=None, access_token=None, **kw):
        try:
            ticket_sudo = self._document_check_access(
                "helpdesk.ticket", ticket_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        if not ticket_sudo.team_id.allow_portal_ticket_closing:
            raise UserError(
                _("The team does not allow ticket reopening through portal")
            )

        if not ticket_sudo.stage_id.is_close:
            return request.redirect(f"/my/ticket/{ticket_id}/{access_token or ''}")

        team_id = ticket_sudo.team_id
        stage_id = team_id._determine_stage()[team_id.id]

        ticket_sudo.write(
            {
                "stage_id": stage_id.id,
                "closed_by_partner": False,
            }
        )
        body = _("Ticket reopened by the customer")
        ticket_sudo.with_context(mail_create_nosubscribe=True).message_post(
            body=body, message_type="comment", subtype_xmlid="mail.mt_note"
        )

        return request.redirect(f"/my/ticket/{ticket_id}/{access_token or ''}")
