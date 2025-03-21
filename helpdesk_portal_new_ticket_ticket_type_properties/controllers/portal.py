from odoo import http
from odoo.http import request

from odoo.addons.helpdesk_portal_new_ticket.controllers.portal import (
    NewTicketCustomerPortal,
)


class CustomerPortal(NewTicketCustomerPortal):
    def _new_ticket_get_ticket_extra_values(self, **kwargs):
        res = super()._new_ticket_get_ticket_extra_values(**kwargs)

        if not kwargs.get("category"):
            return res

        ticket_type_id = (
            request.env["helpdesk.ticket.category"]
            .sudo()
            .browse(int(kwargs.get("category")))
        )
        if ticket_type_id.ticket_type_properties_definition:
            res.update(
                {
                    "ticket_type_properties": ticket_type_id.ticket_type_properties_definition  # noqa: E501
                }
            )
        return res

    @http.route(
        ["/my/tickets/get_ticket_type_info"],
        type="json",
        auth="user",
        methods=["POST"],
    )
    def get_ticket_type_info(self, ticket_type_id=None, **kwargs):
        ticket_type_id = (
            request.env["helpdesk.ticket.category"]
            .sudo()
            .search([("id", "=", int(ticket_type_id))])
        )

        rendered = request.env["ir.qweb"]._render(
            "helpdesk_portal_new_ticket_ticket_type_properties.portal_helpdesk_ticket_create_ticket_type_properties",  # noqa: E501
            {
                "ticket_type_properties": ticket_type_id.ticket_type_properties_definition  # noqa: E501
            },
        )

        return {
            "template": rendered,
        }

    def _new_helpdesk_ticket_post_hook(self, ticket_id, **kwargs):
        res = super()._new_helpdesk_ticket_post_hook(ticket_id, **kwargs)

        ticket_type_properties = ticket_id.ticket_type_properties

        for ticket_property in ticket_type_properties:
            if ticket_property["type"] == "tags":
                kwargs_property_name = request.httprequest.form.getlist(
                    "ticket_type_property_%s" % ticket_property["name"]
                )
            else:
                kwargs_property_name = kwargs.get(
                    "ticket_type_property_%s" % ticket_property["name"]
                )
            if not kwargs_property_name:
                continue

            if ticket_property["type"] == "integer":
                kwargs_property_name = int(kwargs_property_name)

            if ticket_property["type"] == "float":
                kwargs_property_name = float(kwargs_property_name)

            if ticket_property["type"] == "boolean":
                kwargs_property_name = bool(kwargs_property_name)

            ticket_property["value"] = kwargs_property_name

        ticket_id.write({"ticket_type_properties": ticket_type_properties})
        return res
