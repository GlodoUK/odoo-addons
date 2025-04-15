from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    ecommerce_requires_login = fields.Boolean(default=False)
    ecommerce_requires_login_status_code = fields.Selection(
        [
            ("302", "302 Found"),
            ("303", "303 See Other"),
            ("307", "307 Temporary Redirect"),
        ],
        default="302",
    )
