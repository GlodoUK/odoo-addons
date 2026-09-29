from odoo import fields, models
from odoo.tools import SQL


class HelpdeskTicketReport(models.Model):
    _inherit = "helpdesk.ticket.report.analysis"

    commercial_partner_id = fields.Many2one("res.partner", store=True)

    def _select(self):
        return SQL(
            "%s, T.commercial_partner_id AS commercial_partner_id",
            super()._select(),
        )
