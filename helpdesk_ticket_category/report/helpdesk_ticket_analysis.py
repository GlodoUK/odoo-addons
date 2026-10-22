from odoo import fields, models
from odoo.tools import SQL


class HelpdeskTicketReport(models.Model):
    _inherit = "helpdesk.ticket.report.analysis"

    ticket_categ_id = fields.Many2one(
        "helpdesk.ticket.category",
        "Category",
        readonly=True,
    )

    def _select(self):
        return SQL("%s, T.ticket_categ_id AS ticket_categ_id", super()._select())
