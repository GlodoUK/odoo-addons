from odoo import fields, models


class HelpdeskSLA(models.Model):
    _inherit = "helpdesk.sla"

    ticket_categ_ids = fields.Many2many(
        "helpdesk.ticket.category",
        string="Categories",
    )
