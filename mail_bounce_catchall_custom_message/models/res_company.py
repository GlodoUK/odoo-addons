from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    use_custom_catchall_bounce_message = fields.Boolean(default=False)
    custom_catchall_bounce_message = fields.Html()
