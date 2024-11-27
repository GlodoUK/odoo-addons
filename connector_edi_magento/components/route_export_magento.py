import logging

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component
from odoo.addons.connector_edi.mixins import MixinJobFromCtx, MixinSafeFormatPath

_logger = logging.getLogger(__name__)


class EdiRouteMagentoExporterComponent(Component, MixinSafeFormatPath, MixinJobFromCtx):
    _name = "edi.route.exporter.magento"
    _inherit = ["base.exporter", "edi.connector"]
    _usage = "export.magento"
    _apply_on = "edi.envelope"

    def run(self, route_id, **kwargs):
        backend = self.backend_record
        endpoint = route_id.magento_endpoint
        method = kwargs.get("method", "POST")
        if not endpoint:
            raise UserError(_("No endpoint specified"))
        for envelope in kwargs.get("envelope_ids"):
            _logger.info("Pushing to Magento %s for backend %s", endpoint, backend.name)
            response = backend.magento_send_request(
                endpoint, method=method, data=envelope.body
            )
            if not response.status_code == 200:
                envelope.message_post(body=response.content)
                raise UserError(
                    _(
                        "Cannot push Envelope {envelope_id}. Response code"
                        " {status_code}"
                    ).format(envelope_id=envelope.id, status_code=response.status_code)
                )

            self.handle_response(endpoint, response, backend)

            envelope.action_done()

    def handle_response(self, endpoint, response, backend):
        if endpoint == "products/":
            self.env["product.template"].handle_magento_response(response, backend)
        elif endpoint == "orders/":
            self.env["sale.order"].handle_magento_response(response, backend)
