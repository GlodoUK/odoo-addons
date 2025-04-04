from odoo import http
from odoo.http import request

from odoo.addons.helpdesk_portal_new_ticket.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    def _new_ticket_get_page_view_values(self, **kwargs):
        res = super()._new_ticket_get_page_view_values(**kwargs)

        if not res.get("default_category"):
            return res

        ticket_type_id = (
            request.env["helpdesk.ticket.category"]
            .sudo()
            .browse(int(res.get("default_category")))
        )

        if ticket_type_id.ticket_type_properties_definition:
            res.update(
                {
                    "ticket_type_properties_initial": ticket_type_id.ticket_type_properties_definition  # noqa: E501
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

        ticket_type_properties = ticket_type_id.ticket_type_properties_definition  # noqa: E501

        rendered = request.env["ir.qweb"]._render(
            "helpdesk_portal_new_ticket_ticket_type_properties.portal_helpdesk_ticket_create_ticket_type_properties",  # noqa: E501
            {"ticket_type_properties": ticket_type_properties},
        )

        return {
            "template": rendered,
        }

    def _new_helpdesk_ticket_post_hook(self, ticket_id, **kwargs):
        res = super()._new_helpdesk_ticket_post_hook(ticket_id, **kwargs)

        ticket_type_properties = ticket_id.ticket_type_properties

        for prop in ticket_id.ticket_categ_id.ticket_type_properties_definition:
            if prop["type"] == "tags":
                kwargs_property_name = request.httprequest.form.getlist(
                    f"ticket_type_property_{prop['name']}"
                )
            else:
                kwargs_property_name = kwargs.get(
                    f"ticket_type_property_{prop['name']}"
                )
            if not kwargs_property_name:
                continue

            if prop["type"] in ("char", "date", "datetime"):
                ticket_type_properties[prop["name"]] = kwargs_property_name

            if prop["type"] == "boolean":
                ticket_type_properties[prop["name"]] = bool(kwargs_property_name)

            if prop["type"] == "integer":
                ticket_type_properties[prop["name"]] = int(kwargs_property_name)

            if prop["type"] == "float":
                ticket_type_properties[prop["name"]] = float(kwargs_property_name)

            if prop["type"] == "selection":
                for option in prop["selection"]:
                    if option[0] == kwargs_property_name:
                        ticket_type_properties[prop["name"]] = option[0]
                        continue

            if prop["type"] == "tags":
                options = []
                for option in prop["tags"]:
                    if option[0] == kwargs_property_name:
                        options.append(option[0])

                ticket_type_properties[prop["name"]] = options

        ticket_id.write({"ticket_type_properties": ticket_type_properties})

        return res
