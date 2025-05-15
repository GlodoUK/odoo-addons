from odoo.addons.component.core import Component


class EdiRouteScpImporterComponent(Component):
    _name = "edi.route.scp.importer"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "import.scp"
    _apply_on = "edi.envelope"

    def run(self, route_id, **kwargs):
        raise NotImplementedError()
