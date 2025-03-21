from odoo import fields, models


class HelpdeskTicketCategory(models.Model):
    _inherit = "helpdesk.ticket.category"

    ticket_type_properties_definition = fields.PropertiesDefinition(
        "Ticket Category Properties"
    )


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_type_properties = fields.Properties(
        definition="ticket_categ_id.ticket_type_properties_definition",
    )
