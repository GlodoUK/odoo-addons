from odoo.http import request

from odoo.addons.auth_oauth.controllers.main import OAuthLogin


class OAuthLoginRestricted(OAuthLogin):
    def list_providers(self):
        res = super().list_providers()

        filtered = []

        for provider in res:
            oauth_id = request.env["auth.oauth.provider"].sudo().browse(provider["id"])
            valid_website_ids = oauth_id.restrict_to_website_ids
            if not valid_website_ids or request.website in valid_website_ids:
                filtered.append(provider)

        return filtered
