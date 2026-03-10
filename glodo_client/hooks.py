import logging

from odoo import http

_logger = logging.getLogger(__name__)


# https://github.com/odoo/odoo/issues/7766
def _post_load():
    _logger.info("Applying monkey patch for Odoo Issue #7766 (JSON hijacking)...")
    original_get_request = http.Root.get_request

    def get_request(self, httprequest):
        if httprequest.mimetype == "application/json" and httprequest.path.startswith(
            "/glodo_cloud/"
        ):
            return http.HttpRequest(httprequest)
        return original_get_request(self, httprequest)

    http.Root.get_request = get_request
