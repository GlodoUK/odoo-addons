from odoo import fields, models
from odoo.tools import plaintext2html


class HelpdeskTicketCategory(models.Model):
    _inherit = "helpdesk.ticket.category"

    ticket_type_properties_definition = fields.PropertiesDefinition(
        "Ticket Properties",
    )


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_type_properties = fields.Properties(
        definition="ticket_categ_id.ticket_type_properties_definition"
    )

    def _display_ticket_type_properties(self):
        self.ensure_one()

        res = []

        ticket_type_properties = self.ticket_type_properties

        if not ticket_type_properties:
            return res

        for prop_map in self.ticket_categ_id.ticket_type_properties_definition:
            if any(not prop_map.get(key) for key in ("name", "type", "string")):
                continue

            prop_map_dict = {
                "display_title": prop_map["string"],
                "display_value": False,
                "display_suffix": prop_map.get("suffix", False),
            }

            if prop_map["type"] in (
                "char",
                "date",
                "datetime",
                "selection",
                "tags",
            ):
                prop_map_dict.update(
                    {
                        "display_value": ticket_type_properties[prop_map["name"]],
                    }
                )

            if prop_map["type"] in (
                "boolean",
                "float",
                "integer",
            ):
                prop_map_dict.update(
                    {
                        "display_value": str(ticket_type_properties[prop_map["name"]]),
                    }
                )

            if prop_map["type"] in (
                "float",
                "integer",
            ):
                prop_map_dict.update(
                    {
                        "display_value": ticket_type_properties[prop_map["name"]]
                        or "0",
                    }
                )

            if prop_map["type"] in ("text",):
                prop_map_dict.update(
                    {
                        "display_value": plaintext2html(
                            ticket_type_properties[prop_map["name"]]
                        )
                        if ticket_type_properties[prop_map["name"]]
                        else False,
                        "display_suffix": False,
                    }
                )

            if (
                prop_map["type"] in ("many2one", "many2many")
                and "comodel" in prop_map
                and prop_map["comodel"]
            ):
                prop_map_dict.update(
                    {
                        "display_value": ", ".join(
                            ticket_type_properties[prop_map["name"]].mapped(
                                "display_name"
                            )
                        ),
                    }
                )

            res.append(prop_map_dict)

        return res
