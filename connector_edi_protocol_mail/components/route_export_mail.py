from odoo.addons.component.core import Component


class EdiRouteMailImporterComponent(Component):
    _name = "edi.route.mail.exporter"
    _inherit = ["base.exporter", "edi.connector"]
    _usage = "export.mail"
    _apply_on = "edi.route"

    def run(self, route_id, **kwargs):
        raise NotImplementedError()
