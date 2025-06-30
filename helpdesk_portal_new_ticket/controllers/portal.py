from odoo import http
from odoo.http import request
from odoo.tools import plaintext2html

from odoo.addons.portal.controllers.portal import CustomerPortal

TICKET_PRIORITY = [
    ("0", "Lowest"),
    ("1", "Low"),
    ("2", "Medium"),
    ("3", "High"),
]


class CustomerPortal(CustomerPortal):
    def _prepare_team_ids_domain(self):
        return [
            ("company_id", "in", (False, request.env.company.id)),
            ("privacy_visibility", "=", "portal"),
        ]

    def _prepare_ticket_type_ids_domain(self):
        return []

    def _prepare_team_ids(self):
        domain = self._prepare_team_ids_domain()
        return request.env["helpdesk.team"].sudo().search(domain)

    def _prepare_ticket_type_ids(self):
        domain = self._prepare_ticket_type_ids_domain()
        return request.env["helpdesk.ticket.category"].sudo().search(domain)

    def _prepare_default_category(self):
        return request.env.ref("helpdesk_ticket_category.type_issue").sudo().id

    def _new_ticket_get_page_view_values(self, **kw):
        return {
            "page_name": "ticket_new",
            "default_category": self._prepare_default_category(),
            "default_priority": TICKET_PRIORITY[0][0],
            "team_ids": self._prepare_team_ids(),
            "ticket_type_ids": self._prepare_ticket_type_ids(),
            "priorities": TICKET_PRIORITY,
        }

    def _new_ticket_get_ticket_extra_values(self, **kw):
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
        REQUIRED_FIELDS = ["category", "description", "subject", "team"]

        if any(not kw.get(f) for f in REQUIRED_FIELDS):
            return request.render(
                "helpdesk_portal_new_ticket.template_helpdesk_ticket_new",
                self._new_ticket_get_page_view_values(**kw),
            )

        team_id = (
            request.env["helpdesk.team"].sudo().search([("id", "=", kw.get("team"))])
        )

        values = {
            "partner_id": request.env.user.partner_id.id,
            "team_id": team_id.id,
            "name": kw.get("subject"),
            "description": plaintext2html(kw.get("description")),
            "priority": kw.get("priority", "0"),
            "ticket_categ_id": int(kw.get("category")),
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
