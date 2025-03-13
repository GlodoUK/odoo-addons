from odoo import fields, models


class HelpdeskSLAReport(models.Model):
    _inherit = "helpdesk.sla.report.analysis"

    ticket_categ_id = fields.Many2one(
        "helpdesk.ticket.category",
        string="Category",
        readonly=True,
    )

    def _select(self):
        return super()._select() + ", T.ticket_categ_id AS ticket_categ_id"
