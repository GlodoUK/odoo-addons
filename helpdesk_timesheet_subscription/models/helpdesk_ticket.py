import pytz

from odoo import _, fields, models
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    is_using_timesheets = fields.Boolean(compute="_compute_is_using_timesheets")
    glo_total_hours_spent = fields.Float(related="total_hours_spent")
    glo_last_updated = fields.Char(compute="_compute_glo_last_updated")

    def _compute_glo_last_updated(self):
        for obj in self:
            email_message_ids = obj.message_ids.filtered(
                lambda msg_id: msg_id.message_type in ["email", "comment"]
            )
            last_message = email_message_ids and max(email_message_ids)
            last_updated_val = ""
            if last_message:
                local_tz = pytz.timezone(self._context["tz"])

                msg_write_date = fields.Datetime.to_string(
                    last_message.date.replace(microsecond=0).astimezone(local_tz)
                )
                partner_name = (
                    last_message.mapped("write_uid.partner_id.name")[0]
                    if last_message.mapped("write_uid.partner_id.name")
                    else last_message.write_uid.name
                )
                last_updated_val = f"{msg_write_date} by {partner_name}"
            obj.glo_last_updated = last_updated_val

    def _compute_is_using_timesheets(self):
        """Computes if helpdesk team has timesheets installed to hide/show button"""
        for obj in self:
            if obj.team_id and obj.team_id.use_helpdesk_timesheet:
                obj.is_using_timesheets = True
            else:
                obj.is_using_timesheets = False

    def ensure_has_team_n_product(self):
        """Makes sure that helpdesk team have time replenisher sent"""
        for obj in self:
            if not obj.mapped("team_id.glo_product_id"):
                raise UserError(
                    _(
                        "Please, set up product for helpdesk team '%(team)s'"
                        " in settings"
                    )
                    % {"team": obj.team_id.name}
                )

    def action_post_message_n_log_time(self):
        """Launches wizard that fills timesheet and writes message at the same time"""
        self.ensure_one()
        return {
            "name": _("Post Message And Log Time"),
            "view_mode": "form",
            "view_id": False,
            "view_type": "form",
            "res_model": "glo.post.msg.log.time.wizard",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {"default_helpdesk_ticket_id": self.id},
        }
