from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auth_signup_optional_notify_enable = fields.Boolean(
        string="Notify the Inviter After Signup",
        config_parameter="auth_signup_optional_notify.enable_notification",
    )
