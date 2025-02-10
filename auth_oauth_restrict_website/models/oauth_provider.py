from odoo import fields, models


class OAuthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    restrict_to_website_ids = fields.Many2many(
        "website",
        "auth_oath_provider_restricted_website_rel",
        string="Display on Website",
        help="Leave blank for all",
    )
