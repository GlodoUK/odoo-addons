from odoo import fields, models


class AccountMoveHelpdeskLink(models.Model):
    _inherit = "account.move"

    helpdesk_ticket_id = fields.Many2one(comodel_name="helpdesk.ticket", index=True)
