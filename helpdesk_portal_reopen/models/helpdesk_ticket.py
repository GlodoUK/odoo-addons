from odoo import _, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    def reopen(self):
        for ticket in self:
            team_id = ticket.team_id

            stage_id = (
                team_id.reopen_ticket_stage or team_id._determine_stage()[team_id.id]
            )

            ticket.write(
                {
                    "closed_by_partner": False,
                    "stage_id": stage_id.id,
                }
            )

            if team_id.clear_assigned_on_reopen:
                ticket.write({"user_id": False})

            body = _("Ticket reopened by the customer")

            ticket.with_context(mail_create_nosubscribe=True).message_post(
                body=body, message_type="comment", subtype_xmlid="mail.mt_note"
            )
