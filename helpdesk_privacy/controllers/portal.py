from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.helpdesk.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    @http.route(
        [
            "/helpdesk/ticket/privacy/<int:ticket_id>",
            "/helpdesk/ticket/privacy/<int:ticket_id>/<access_token>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def ticket_privacy(self, ticket_id, access_token=None, **kw):
        try:
            ticket_sudo = self._document_check_access(
                "helpdesk.ticket", ticket_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        # Ensure tracking=True message is posted by request.env.user
        ticket_sudo = ticket_sudo.with_user(request.env.user).sudo()

        ticket_sudo.is_private = not ticket_sudo.is_private

        # Stop request.env.user from locking themselves out of ticket
        ticket_sudo.message_subscribe(partner_ids=request.env.user.partner_id.ids)

        return request.redirect(f"/my/ticket/{ticket_id}/{access_token or ''}")

    @http.route(
        [
            "/helpdesk/ticket/follow/<int:ticket_id>",
            "/helpdesk/ticket/follow/<int:ticket_id>/<access_token>",
        ],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def ticket_follow(self, ticket_id, access_token=None, **kw):
        try:
            ticket_sudo = self._document_check_access(
                "helpdesk.ticket", ticket_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        allowed_partner_ids = ticket_sudo._privacy_possible_followers().ids

        partner_ids = []

        for partner_id in request.httprequest.form.getlist("partner_ids"):
            try:
                if int(partner_id) in allowed_partner_ids:
                    partner_ids.append(partner_id)
            except ValueError:  # pylint: disable=except-pass
                pass

        if partner_ids:
            ticket_sudo.message_subscribe(partner_ids)

        return request.redirect(f"/my/ticket/{ticket_id}/{access_token or ''}")

    @http.route(
        [
            "/helpdesk/ticket/unfollow/<int:ticket_id>",
            "/helpdesk/ticket/unfollow/<int:ticket_id>/<access_token>",
        ],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def ticket_unfollow(self, ticket_id, access_token=None, **kw):
        try:
            ticket_sudo = self._document_check_access(
                "helpdesk.ticket", ticket_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        try:
            if kw.get("partner_id"):
                ticket_sudo.message_unsubscribe([int(kw.get("partner_id", 0))])
        except ValueError:  # pylint: disable=except-pass
            pass

        return request.redirect(f"/my/ticket/{ticket_id}/{access_token or ''}")
