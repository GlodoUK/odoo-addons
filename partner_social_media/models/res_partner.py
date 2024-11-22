from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    social_media_ids = fields.One2many(
        "res.partner.social.media",
        "partner_id",
        string="Social Media",
    )
