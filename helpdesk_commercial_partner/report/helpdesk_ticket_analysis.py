from odoo import fields, models


class HelpdeskTicketReport(models.Model):
    _inherit = "helpdesk.ticket.report.analysis"

    commercial_partner_id = fields.Many2one("res.partner", store=True)

    def _select(self):
        return super()._select() + ", T.commercial_partner_id AS commercial_partner_id"
