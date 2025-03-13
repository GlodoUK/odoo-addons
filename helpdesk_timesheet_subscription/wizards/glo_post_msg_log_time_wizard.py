from odoo import fields, models


class GloPostMsgLogTimeWizard(models.TransientModel):
    _name = "glo.post.msg.log.time.wizard"
    _description = "Glo Post Message Log Time Wizard"

    helpdesk_ticket_id = fields.Many2one(comodel_name="helpdesk.ticket", required=True)
    hours_spent = fields.Float(required=True)
    message = fields.Html(required=True)

    def post_hours_and_message(self):
        """Does double post of hours into Time log and message into ticket"""
        analytic_line_id = (
            self.env["account.analytic.line"]
            .sudo()
            .create(
                {
                    "unit_amount": self.hours_spent,
                    "helpdesk_ticket_id": self.helpdesk_ticket_id.id,
                    "name": f"Message: {self.create_date.replace(microsecond=0)}",
                }
            )
        )
        self.env["mail.message"].sudo().create(
            {
                "subject": f"{self.helpdesk_ticket_id.name} ticket update",
                "body": self.message,
                "author_id": self.env.user.partner_id.id,
                "author_guest_id": False,
                "email_from": f'"{self.env.user.partner_id.name}" '
                f"<{self.env.user.partner_id.email}>",
                "subtype_id": self.env.ref("mail.mt_comment").id,
                "model": "helpdesk.ticket",
                "message_type": "comment",
                "res_id": self.helpdesk_ticket_id.id,
                "glo_analytic_line_id": analytic_line_id.id,
            }
        )
