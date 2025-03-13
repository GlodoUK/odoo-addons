from odoo import fields, models


class HelpdeskTicketReport(models.Model):
    _inherit = "helpdesk.ticket.report.analysis"

    ticket_categ_id = fields.Many2one(
        "helpdesk.ticket.category",
        string="Category",
        readonly=True,
    )

    def _select(self):
        return super()._select() + ", T.ticket_categ_id AS ticket_categ_id"
