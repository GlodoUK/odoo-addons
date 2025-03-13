from odoo import fields, models


class HelpdeskTicketType(models.Model):
    _inherit = "helpdesk.ticket.type"

    ticket_type_properties_definition = fields.PropertiesDefinition(
        "Ticket Type Properties"
    )


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_type_properties = fields.Properties(
        definition="ticket_type_id.ticket_type_properties_definition",
    )
