from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    is_escalated = fields.Boolean(string="Escalated", tracking=True)

    def action_toggle_escalated(self):
        for record in self:
            record.is_escalated = not record.is_escalated
