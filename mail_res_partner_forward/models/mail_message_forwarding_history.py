from odoo import fields, models


class MailMessageForwardingHistory(models.Model):
    _name = "mail.message.forwarding.history"
    _description = ""

    message_id = fields.Many2one(
        "mail.message", required=True, index=True, ondelete="cascade"
    )
    replaced_partner_id = fields.Many2one(
        "res.partner", required=True, ondelete="cascade"
    )
    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
