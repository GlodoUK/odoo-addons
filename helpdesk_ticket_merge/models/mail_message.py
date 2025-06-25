from odoo import api, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            if record.model == "helpdesk.ticket":
                ticket = self.env["helpdesk.ticket"].browse(record.res_id)
                if ticket.merged_into:
                    # If the ticket was merged, we need to update the res_id
                    # to point to the target ticket instead of the original one.
                    target_ticket = ticket.merged_into
                    while target_ticket.merged_into:
                        target_ticket = ticket.merged_into
                    record.write(
                        {
                            "res_id": target_ticket.id,
                            "subject": f"Reply posted to {ticket.name}",
                        }
                    )
        return res
