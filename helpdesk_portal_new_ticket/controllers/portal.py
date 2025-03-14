from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal

TICKET_PRIORITY = [
    ("0", "Lowest"),
    ("1", "Low"),
    ("2", "Medium"),
    ("3", "High"),
]


class NewTicketCustomerPortal(CustomerPortal):
    def _new_ticket_get_page_view_values(self, **kwargs):
        return {
            "page_name": "ticket_new",
            "team_ids": request.env["helpdesk.team"]
            .sudo()
            .search(
                [
                    ("company_id", "in", (False, request.env.company.id)),
                    ("privacy_visibility", "=", "portal"),
                ]
            ),
            "ticket_type_ids": request.env["helpdesk.ticket.type"].sudo().search([]),
            "priorities": TICKET_PRIORITY,
            "default_priority": TICKET_PRIORITY[0][0],
            "default_category": request.env["helpdesk.ticket.type"]
            .sudo()
            .search([("name", "=", "Question")], limit=1)
            .id,
        }

    def _new_ticket_get_ticket_extra_values(self, **kwargs):
        return {}

    @http.route(
        ["/my/tickets/new", "/helpdesk/tickets/new"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
        methods=["GET"],
    )
    def new_helpdesk_ticket(self, **kw):
        return request.render(
            "helpdesk_portal_new_ticket.template_helpdesk_ticket_new",
            self._new_ticket_get_page_view_values(**kw),
        )

    @http.route(
        ["/my/tickets/new", "/helpdesk/tickets/new"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
        methods=["POST"],
    )
    def new_helpdesk_ticket_post(self, **kw):
        REQUIRED_FIELDS = ["team", "subject", "description", "category"]

        if any(not kw.get(f) for f in REQUIRED_FIELDS):
            return request.render(
                "helpdesk_portal_new_ticket.template_helpdesk_ticket_new",
                self._new_ticket_get_page_view_values(**kw),
            )

        team_id = (
            request.env["helpdesk.team"]
            .sudo()
            .search([("id", "=", kw.get("team"))], limit=1)
        )

        values = {
            "partner_id": request.env.user.partner_id.id,
            "team_id": team_id.id,
            "name": kw.get("subject"),
            "description": kw.get("description"),
            "priority": kw.get("priority", "0"),
            "ticket_type_id": int(kw.get("category")),
        }
        values.update(self._new_ticket_get_ticket_extra_values(**kw))

        ticket_id = (
            request.env["helpdesk.ticket"]
            .with_user(request.env.user)
            .sudo()
            .create(values)
        )

        self._new_helpdesk_ticket_post_hook(ticket_id, **kw)

        return request.redirect(f"/my/ticket/{ticket_id.id}")

    def _new_helpdesk_ticket_post_hook(self, ticket_id, **kwargs):
        ticket_id.message_subscribe(partner_ids=request.env.user.partner_id.ids)
