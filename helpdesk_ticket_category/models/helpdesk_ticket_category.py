from odoo import fields, models


class HelpdeskTicketCategory(models.Model):
    _name = "helpdesk.ticket.category"
    _description = "Helpdesk Ticket Category"
    _order = "sequence, name"

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

    _sql_constraints = [
        ("name_uniq", "unique (name)", "A category with the same name already exists."),
    ]
