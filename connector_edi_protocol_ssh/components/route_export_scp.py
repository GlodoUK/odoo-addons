from odoo.addons.component.core import Component
from odoo.addons.connector_edi.mixins import MixinSafeFormatPath


class EdiRouteScpExporterComponent(Component, MixinSafeFormatPath):
    _name = "edi.route.scp.exporter"
    _inherit = ["base.exporter", "edi.connector"]
    _usage = "export.scp"
    _apply_on = "edi.envelope"

    def run(self, route_id, **kwargs):
        raise NotImplementedError()
