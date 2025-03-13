from odoo import api, models


class FollowupMailMessage(models.Model):
    _inherit = "mail.message"

    def auto_update_ticket_stage(self):
        """Triggers automatic ticket stages update"""
        for obj in self:
            if obj.model == "helpdesk.ticket" and obj.message_type == "comment":
                author_user_id = (
                    obj.author_id.user_ids[0] if obj.author_id.user_ids else False
                )
                if author_user_id and obj.res_id:
                    self.env["helpdesk.ticket"].sudo().browse(
                        obj.res_id
                    ).update_ticket_stage(author_user_id)

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        res.auto_update_ticket_stage()
        return res
