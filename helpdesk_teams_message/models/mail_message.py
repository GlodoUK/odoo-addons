from odoo import api, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.model and res.model == "helpdesk.ticket" and res.res_id:
            ticket_id = self.env["helpdesk.ticket"].browse(res.res_id)
            if ticket_id:
                for obj in res:
                    if obj.subtype_id == self.env.ref("mail.mt_comment"):
                        ticket_id.send_webhook_data("message", False, obj.author_id)
        return res
