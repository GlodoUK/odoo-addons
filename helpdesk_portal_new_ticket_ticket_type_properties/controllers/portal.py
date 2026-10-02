from datetime import UTC, datetime

from odoo import fields, http
from odoo.http import request
from odoo.tools import html2plaintext

from odoo.addons.helpdesk_portal_new_ticket.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    def _new_ticket_get_page_view_values(self, **kwargs):
        res = super()._new_ticket_get_page_view_values(**kwargs)

        if not res.get("default_categ_id"):
            return res

        ticket_type_id = (
            request.env["helpdesk.ticket.category"]
            .sudo()
            .browse(int(res.get("default_categ_id")))
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
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def get_ticket_type_info(self, ticket_type_id=None, **kwargs):
        ticket_type_id = (
            request.env["helpdesk.ticket.category"]
            .sudo()
            .search([("id", "=", int(ticket_type_id))])
        )

        ticket_type_properties = ticket_type_id.ticket_type_properties_definition

        rendered = request.env["ir.qweb"]._render(
            "helpdesk_portal_new_ticket_ticket_type_properties.portal_helpdesk_ticket_create_ticket_type_properties",
            {"ticket_type_properties": ticket_type_properties},
        )

        return {
            "template": rendered,
        }

    def _new_helpdesk_ticket_post_hook(self, ticket_id, **kwargs):
        res = super()._new_helpdesk_ticket_post_hook(ticket_id, **kwargs)

        values = dict(ticket_id.ticket_type_properties)

        for prop in ticket_id.ticket_categ_id.ticket_type_properties_definition:
            if prop["type"] == "tags":
                kwargs_property_name = request.httprequest.form.getlist(
                    f"ticket_type_property_{prop['name']}"
                )
            else:
                kwargs_property_name = kwargs.get(
                    f"ticket_type_property_{prop['name']}"
                )
            if prop["type"] == "boolean":
                # an unticked checkbox is not posted at all
                values[prop["name"]] = bool(kwargs_property_name)
                continue

            if not kwargs_property_name:
                continue

            if prop["type"] in ("char", "date"):
                values[prop["name"]] = kwargs_property_name

            if prop["type"] == "datetime":
                values[prop["name"]] = self._ticket_type_property_to_datetime(
                    kwargs_property_name
                )

            if prop["type"] == "integer":
                values[prop["name"]] = int(kwargs_property_name)

            if prop["type"] == "float":
                values[prop["name"]] = float(kwargs_property_name)

            if prop["type"] == "selection":
                for option in prop.get("selection", []):
                    if option[0] == kwargs_property_name:
                        values[prop["name"]] = option[0]
                        continue

            if prop["type"] == "tags":
                options = []
                for option in prop.get("tags", []):
                    if option[0] in kwargs_property_name:
                        options.append(option[0])
                values[prop["name"]] = options

            if prop["type"] == "text":
                values[prop["name"]] = html2plaintext(kwargs_property_name)

        ticket_id.write({"ticket_type_properties": values})

        return res

    def _ticket_type_property_to_datetime(self, value):
        # <input type="datetime-local"> posts the customer's wall-clock time
        # ("2026-10-01T14:30"), datetime properties hold UTC server strings
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return False
        if not value.tzinfo:
            value = value.replace(tzinfo=request.env.tz)
        return fields.Datetime.to_string(value.astimezone(UTC).replace(tzinfo=None))
