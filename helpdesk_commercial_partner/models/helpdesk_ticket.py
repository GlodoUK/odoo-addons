from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    commercial_partner_id = fields.Many2one(store=True)
