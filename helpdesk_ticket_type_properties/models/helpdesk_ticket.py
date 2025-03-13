from odoo import fields, models


class HelpdeskTicketType(models.Model):
    _inherit = "helpdesk.ticket.type"

    ticket_type_properties_definition = fields.PropertiesDefinition("Ticket Properties")


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_type_properties = fields.Properties(
        definition="ticket_type_id.ticket_type_properties_definition"
    )

    def _display_ticket_type_properties(self):
        self.ensure_one()

        res = []

        ticket_type_properties = self.ticket_type_properties

        for prop_map in self.ticket_type_id.ticket_type_properties_definition:
            if any(key not in prop_map for key in ("name", "type", "string")):
                continue

            if prop_map["type"] in (
                "bool",
                "char",
                "date",
                "datetime",
                "float",
                "integer",
            ):
                res.append(
                    {
                        "display_title": prop_map["string"],
                        "display_value": ticket_type_properties[prop_map["name"]],
                    }
                )

            if (
                prop_map["type"] in ("many2one", "many2many")
                and "comodel" in prop_map
                and prop_map["comodel"]
            ):
                recordset = self.env[prop_map["comodel"]].browse(
                    ticket_type_properties[prop_map["name"]]
                )

                res.append(
                    {
                        "display_title": prop_map["string"],
                        "display_value": ", ".join(recordset.mapped("display_name")),
                    }
                )

            if (
                prop_map["type"] in ("selection")
                and "selection" in prop_map
                and prop_map["selection"]
            ):
                display_value = False
                selected_value = ticket_type_properties[prop_map["name"]]

                for option in prop_map["selection"]:
                    if option[0] == selected_value:
                        display_value = option[1]
                        continue

                res.append(
                    {
                        "display_title": prop_map["string"],
                        "display_value": display_value,
                    }
                )

            if prop_map["type"] in ("tags") and "tags" in prop_map and prop_map["tags"]:
                selected_value = ticket_type_properties.get(prop_map["name"], [])

                if not isinstance(selected_value, list):
                    selected_value = [selected_value] if selected_value else []

                selected_tags = [
                    label
                    for tag_id, label, _ in prop_map["tags"]
                    if tag_id in selected_value
                ]

                res.append(
                    {
                        "display_title": prop_map["string"],
                        "display_value": ", ".join(selected_tags),
                    }
                )

        return res
