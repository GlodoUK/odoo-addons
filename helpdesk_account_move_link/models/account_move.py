from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    helpdesk_ticket_ids = fields.Many2many(
        "helpdesk.ticket",
        "account_move_helpdesk_ticket_rel",
        "account_move_id",
        "helpdesk_ticket_id",
    )
