from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    message_count = fields.Integer(compute="_compute_message_count", store=True)

    @api.depends("message_ids")
    def _compute_message_count(self):
        for record in self:
            record.message_count = len(record.message_ids)
