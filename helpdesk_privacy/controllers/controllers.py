from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.helpdesk_portal_new_ticket.controllers.portal import (
    NewTicketCustomerPortal,
)


class CustomerPortalHelpdeskPrivacy(NewTicketCustomerPortal):
    def _new_ticket_get_page_view_values(self, **kwargs):
        res = super()._new_ticket_get_page_view_values(**kwargs)

        res.update(
            {
                "privacy": kwargs.get("privacy", None),
            }
        )

        return res

    @http.route(
        ["/helpdesk/ticket/privacy/<int:ticket_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def ticket_toggle_privacy(self, ticket_id, **kw):
        try:
            ticket_sudo = self._document_check_access(
                "helpdesk.ticket", ticket_id, None
            )
            # this looks wonky, it's to ensure that we post the tracking with the
            # correct user, whilst using leaning on _document_check_access.
            ticket_sudo = ticket_sudo.with_user(request.env.user).sudo()
        except (AccessError, MissingError):
            return request.redirect("/my")

        ticket_sudo.is_private = not ticket_sudo.is_private
        # ensure that the current user is subscribed, so they dont lock
        # themselves out of the ticket
        ticket_sudo.message_subscribe(partner_ids=request.env.user.partner_id.ids)
        return request.redirect(f"/helpdesk/ticket/{ticket_id}")

    @http.route(
        ["/helpdesk/ticket/unfollow/<int:ticket_id>"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def ticket_unfollow(self, ticket_id, **kw):
        try:
            ticket_sudo = self._document_check_access(
                "helpdesk.ticket", ticket_id, None
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        try:
            if kw.get("partner_id"):
                ticket_sudo.message_unsubscribe([int(kw.get("partner_id", 0))])
        except ValueError:  # pylint: disable=except-pass
            pass

        return request.redirect(f"/helpdesk/ticket/{ticket_id}")

    @http.route(
        ["/helpdesk/ticket/follow/<int:ticket_id>"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def ticket_follow(self, ticket_id, **kw):
        try:
            ticket_sudo = self._document_check_access(
                "helpdesk.ticket", ticket_id, None
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        partner_ids = []

        possible_partner_ids = ticket_sudo._privacy_possible_followers().ids

        for i in request.httprequest.form.getlist("partner_ids"):
            try:
                i = int(i)
                if i in possible_partner_ids:
                    partner_ids.append(i)
            except ValueError:  # pylint: disable=except-pass
                pass

        if partner_ids:
            ticket_sudo.message_subscribe(partner_ids)

        return request.redirect(f"/helpdesk/ticket/{ticket_id}")
