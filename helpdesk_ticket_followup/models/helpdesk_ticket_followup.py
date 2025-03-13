import logging

from odoo import fields, models

_logger = logging.getLogger("odoo")

# Maps is sent field in ticket followup model to the options in res.partner settings
IS_SENT_BOOL_USR_OPTION = {
    "is_1st_sent": "is_send_followup_1st",
    "is_2nd_sent": "is_send_followup_2nd",
}
# Maps is sent field in ticket followup model to the options
IS_SENT_BOOL_MAIL_TMP_FIELDS = {
    "is_1st_sent": "glo_followup_mail_temp_1st",
    "is_2nd_sent": "glo_followup_mail_temp_2nd",
}


class HelpdeskTicketFollowup(models.Model):
    _name = "helpdesk.ticket.followup"
    _description = "Helpdesk Ticket Followup"

    helpdesk_ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket", ondelete="cascade"
    )
    date_start = fields.Datetime(
        default=lambda self: fields.Datetime.now(), required=True
    )
    is_1st_sent = fields.Boolean(string="1st Msg Sent")
    is_2nd_sent = fields.Boolean(string="2nd Msg Sent")

    def reset_ticket_followup(self):
        """Resets ticket followups like it was just created"""
        self.write(
            {
                "date_start": fields.Datetime.now(),
                "is_1st_sent": False,
                "is_2nd_sent": False,
            }
        )

    def send_followup_email(self, followup_partner_ids, mail_template):
        """Sends followup email for followup partners"""
        self.ensure_one()
        email_values = {"email_to": False, "recipient_ids": followup_partner_ids.ids}
        mail_template.send_mail(
            self.helpdesk_ticket_id.id, force_send=True, email_values=email_values
        )

    def get_first_second_close_time(self):
        """Gets first, second message closing time"""
        params = self.env["ir.config_parameter"].sudo()
        first_time = int(
            params.get_param("helpdesk_ticket_followup.glo_1st_followup_hrs", default=0)
        )
        second_time = int(
            params.get_param("helpdesk_ticket_followup.glo_2nd_followup_hrs", default=0)
        )
        close_time = int(
            params.get_param(
                "helpdesk_ticket_followup.glo_close_automatically_hrs", default=0
            )
        )
        return first_time, second_time, close_time

    def prepare_and_run_n_time_email_followups(self, n_time, is_sent_field):
        self.ensure_one()
        if not self[is_sent_field]:
            followup_partner_ids = self.helpdesk_ticket_id.mapped(
                "message_follower_ids.partner_id"
            )
            # Filtering out subscribers that turned off followup or
            # snoozed notifications
            followup_partner_ids = followup_partner_ids.filtered(
                lambda fp_id: fp_id[IS_SENT_BOOL_USR_OPTION[is_sent_field]]
                and (
                    not fp_id.snooze_till_date
                    or fp_id.snooze_till_date < fields.Date.today()
                )
            )
            if followup_partner_ids:
                mail_template_id = self.helpdesk_ticket_id.stage_id[
                    IS_SENT_BOOL_MAIL_TMP_FIELDS[is_sent_field]
                ]
                _logger.info(
                    "- Sending mail template %s in %dh for ticket %s",
                    mail_template_id,
                    n_time,
                    self.helpdesk_ticket_id,
                )
                self.send_followup_email(followup_partner_ids, mail_template_id)
                self[is_sent_field] = True

    def auto_ticket_followup(self):
        """Automatically sends email followups helpdesk ticket customer
        and his subscribed colleagues who have followup option on,
        closes ticket in hrs, which we set in settings."""
        followup_ids = self.env["helpdesk.ticket.followup"].sudo().search([])
        for obj in followup_ids:
            if obj.helpdesk_ticket_id.stage_id.glo_stage_type == "customer_update":
                date_start = obj.date_start
                date_now = fields.Datetime.now()
                # Closing tickets /unlinking followup records that are
                # older than 3 days
                # TODO freeze ticket from here, do we consider weekend?
                time_passed = date_now - date_start
                time_passed_hrs = int(
                    time_passed.seconds / 3600 + time_passed.days * 24
                )
                first_time, second_time, close_time = self.get_first_second_close_time()
                if close_time and time_passed_hrs >= close_time:
                    close_stage_id = obj.helpdesk_ticket_id.return_stage_by_type(
                        "closed"
                    )
                    if obj.helpdesk_ticket_id.stage_id != close_stage_id:
                        obj.helpdesk_ticket_id.stage_id = close_stage_id.id
                    obj.unlink()
                    continue
                if first_time and time_passed_hrs >= first_time:
                    obj.prepare_and_run_n_time_email_followups(
                        first_time, "is_1st_sent"
                    )
                if second_time and time_passed_hrs >= second_time:
                    obj.prepare_and_run_n_time_email_followups(
                        second_time, "is_2nd_sent"
                    )
