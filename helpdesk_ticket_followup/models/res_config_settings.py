from odoo import _, api, fields, models
from odoo.exceptions import UserError

FIELDS_BOOL_HRS = {
    "glo_is_send_1st_followup": "glo_1st_followup_hrs",
    "glo_is_send_2nd_followup": "glo_2nd_followup_hrs",
    "glo_is_close_automatically": "glo_close_automatically_hrs",
}


class FollowupResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    glo_is_send_1st_followup = fields.Boolean(string="Send 1st Followup email")
    glo_is_send_2nd_followup = fields.Boolean(string="Send 2nd Followup email")
    glo_is_close_automatically = fields.Boolean(string="Close automatically")
    glo_is_user_followup_mod = fields.Boolean(string="User Modificator")
    glo_1st_followup_hrs = fields.Integer(string="1st Flollowup in Hours")
    glo_2nd_followup_hrs = fields.Integer(string="2nd Flollowup in Hours")
    glo_close_automatically_hrs = fields.Integer(string="Close Automatically In Hours")

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env["ir.config_parameter"].sudo()
        for field_bool, field_hr in FIELDS_BOOL_HRS.items():
            res.update(
                {
                    field_bool: params.get_param(
                        f"helpdesk_ticket_followup.{field_bool}", default=False
                    ),
                    field_hr: int(
                        params.get_param(
                            f"helpdesk_ticket_followup.{field_hr}", default=0
                        )
                    ),
                }
            )
        res.update(
            {
                "glo_is_user_followup_mod": params.get_param(
                    "helpdesk_ticket_followup.glo_is_user_followup_mod", default=False
                ),
            }
        )
        return res

    def _sanitize_incoming_values(self):
        """Turns off boolean fields if admin set notifications in 0 hrs or fewer"""
        if (
            self.glo_1st_followup_hrs
            and self.glo_2nd_followup_hrs
            and self.glo_1st_followup_hrs >= self.glo_2nd_followup_hrs
        ):
            raise UserError(
                _(
                    "Hours of sending first followup email can't be higher than"
                    " second followup email."
                )
            )
        write_values_dict = {}
        for field_bool, field_hr in FIELDS_BOOL_HRS.items():
            if self[field_bool] and self[field_hr] and self[field_hr] > 0:
                write_values_dict.update(
                    {
                        field_bool: True,
                        field_hr: self[field_hr],
                    }
                )
            else:
                write_values_dict.update(
                    {
                        field_bool: False,
                        field_hr: 0,
                    }
                )
        if write_values_dict:
            self.write(write_values_dict)

    def set_values(self):
        res = super().set_values()
        self._sanitize_incoming_values()
        for field_bool, field_hr in FIELDS_BOOL_HRS.items():
            self.env["ir.config_parameter"].sudo().set_param(
                f"helpdesk_ticket_followup.{field_bool}", self[field_bool]
            )
            self.env["ir.config_parameter"].sudo().set_param(
                f"helpdesk_ticket_followup.{field_hr}", self[field_hr]
            )
        self.env["ir.config_parameter"].sudo().set_param(
            "helpdesk_ticket_followup.glo_is_user_followup_mod",
            self.glo_is_user_followup_mod,
        )
        return res
