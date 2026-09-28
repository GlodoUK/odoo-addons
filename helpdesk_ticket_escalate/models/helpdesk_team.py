from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    escalate_message_partner_ids = fields.Many2many(
        "res.partner",
        string="Escalated Followers (Partners)",
    )
