from odoo import fields, models


class ResPartnerUpdate(models.Model):
    _name = "res.partner.update"
    _description = "Partner Update"
    _order = "id desc"

    name = fields.Char(
        required=True,
    )

    date = fields.Date(
        default=fields.Date.context_today,
    )

    description = fields.Html()

    partner_id = fields.Many2one(
        "res.partner",
        required=True,
    )

    user_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        required=True,
    )
