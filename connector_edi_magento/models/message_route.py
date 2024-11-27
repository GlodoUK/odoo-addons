from odoo import api, fields, models

from ..data.default_order_in_route import DEFAULT_ORDER_IN_ROUTE
from ..data.default_product_in_route import DEFAULT_PRODUCT_IN_ROUTE
from ..data.default_product_out_route import DEFAULT_PRODUCT_OUT_ROUTE


class EnvelopeRoute(models.Model):
    _inherit = "edi.route"

    is_magento = fields.Boolean(related="envelope_route_id.is_magento", store=True)

    def _get_default_route_code(self, route):
        route_map = {
            "product_in": DEFAULT_PRODUCT_IN_ROUTE,
            "product_out": DEFAULT_PRODUCT_OUT_ROUTE,
            "order_in": DEFAULT_ORDER_IN_ROUTE,
        }
        return route_map.get(route, "")

    @api.onchange("action")
    def _onchange_action(self):
        if (
            self.action == "code"
            and self.is_magento
            and self.direction == "in"
            and not self.action_code
            and self.envelope_route_id.magento_endpoint == "products/"
        ):
            self.action_code = self._get_default_route_code("product_in")
        elif (
            self.action == "code"
            and self.is_magento
            and self.direction == "out"
            and not self.action_code
            and self.envelope_route_id.magento_endpoint == "products/"
        ):
            self.action_code = self._get_default_route_code("product_out")
        elif (
            self.action == "code"
            and self.is_magento
            and self.direction == "in"
            and not self.action_code
            and self.envelope_route_id.magento_endpoint == "orders/"
        ):
            self.action_code = self._get_default_route_code("order_in")
