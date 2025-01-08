from odoo import fields, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    forwarded_partner_history_ids = fields.One2many(
        "mail.message.forwarding.history", "message_id"
    )
