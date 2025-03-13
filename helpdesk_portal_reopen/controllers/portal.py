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

        if not ticket_sudo.team_id.allow_portal_ticket_reopen:
            raise UserError(
                _("The team does not allow ticket reopening through portal")
            )

        if ticket_sudo.stage_id.fold:
            ticket_sudo.reopen()

        return request.redirect(f"/my/ticket/{ticket_id}/{access_token or ''}")
