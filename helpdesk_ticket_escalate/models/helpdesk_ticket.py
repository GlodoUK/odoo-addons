from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    is_escalated = fields.Boolean(
        string="Escalated",
        tracking=True,
    )

    def action_toggle_escalated(self):
        for ticket in self:
            ticket.is_escalated = not ticket.is_escalated
