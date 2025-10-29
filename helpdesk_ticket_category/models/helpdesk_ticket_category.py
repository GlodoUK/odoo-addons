from odoo import fields, models


class HelpdeskTicketCategory(models.Model):
    _name = "helpdesk.ticket.category"
    _description = "Helpdesk Ticket Category"
    _order = "sequence, name"

    _name_uniq = models.Constraint(
        "unique (name)",
        "A category with the same name already exists.",
    )

    active = fields.Boolean(
        default=True,
    )

    sequence = fields.Integer(
        default=10,
    )

    name = fields.Char(
        required=True,
        translate=True,
    )
