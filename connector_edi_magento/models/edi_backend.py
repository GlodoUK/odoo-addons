from urllib.parse import urljoin

import requests
from oauthlib.oauth1 import SIGNATURE_HMAC_SHA256
from requests_oauthlib import OAuth1

from odoo import _, fields, models
from odoo.exceptions import UserError


class EdiBackend(models.Model):
    _inherit = "edi.backend"

    is_magento = fields.Boolean(string="Backend Uses Magento", default=False)
    magento_oauth_base_url = fields.Char(
        string="Magento URL", default="https://_magento_url_/"
    )
    magento_oauth_consumer_key = fields.Char(string="Consumer Key")
    magento_oauth_consumer_secret = fields.Char(string="Consumer Secret")
    magento_oauth_token = fields.Char(string="Access Token")
    magento_oauth_token_secret = fields.Char(string="Access Token Secret")

    def _get_magento_rest_url(self, site="all"):
        for record in self:
            return urljoin(record.magento_oauth_base_url, "rest/%s/V1/" % site)

    def _get_magento_session(self):
        self.ensure_one()
        if not self.is_magento:
            raise UserError(_("This backend is not a Magento backend"))
        if (
            not self.magento_oauth_consumer_key
            or not self.magento_oauth_consumer_secret
        ):
            raise UserError(
                _("No Consumer Key or Consumer Secret set for this backend.")
            )
        if not self.magento_oauth_token or not self.magento_oauth_token_secret:
            raise UserError(
                _("No Access Token or Access Token Secret set for this backend.")
            )
        return OAuth1(
            client_key=self.magento_oauth_consumer_key,
            client_secret=self.magento_oauth_consumer_secret,
            resource_owner_key=self.magento_oauth_token,
            resource_owner_secret=self.magento_oauth_token_secret,
            signature_method=SIGNATURE_HMAC_SHA256,
        )

    def magento_send_request(
        self, endpoint, method="GET", params=None, data=None, site="all", timeout=20
    ):
        self.ensure_one()
        oauth = self._get_magento_session()
        url = urljoin(self._get_magento_rest_url(site=site), endpoint)
        function = getattr(requests, method.lower())
        headers = None
        if method.lower() in ["post", "put"]:
            headers = {"Content-Type": "application/json"}
        response = function(
            url, auth=oauth, params=params, data=data, headers=headers, timeout=timeout
        )
        if not response.status_code == 200:
            raise UserError(_("Error sending request to Magento: %s") % response.text)
        return response
