from odoo import api, fields, models

DEADLINE_SECS = 2


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model
    def create(self, vals):
        res = super().create(vals)

        if res.model and res.model == "helpdesk.ticket" and res.res_id:
            ticket = self.env["helpdesk.ticket"].browse(res.res_id)

            # do not touch the ticket if it's been created within the last few
            # seconds
            if (
                ticket.create_date
                and (fields.Datetime.now() - ticket.create_date).seconds
                <= DEADLINE_SECS
            ):
                return res

            # we need to "touch" the ticket to bump the write_date and write_uid
            # for version 12.0
            ticket.write({})

        return res
