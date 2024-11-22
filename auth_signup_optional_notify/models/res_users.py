from odoo import models
from odoo.tools import str2bool


class ResUsers(models.Model):
    _inherit = "res.users"

    def _notify_inviter(self):
        enabled = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("auth_signup_optional_notify.enable_notification", "False")
        )
        if str2bool(enabled):
            return super()._notify_inviter()
