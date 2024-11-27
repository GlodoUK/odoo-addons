from odoo.addons.component.core import Component


class EdiRouteMailImporterComponent(Component):
    _name = "edi.route.mail.importer"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "import.mail"
    _apply_on = "edi.route"

    def run(self, route_id, **kwargs):
        # This is a no-op. Everything runs through edi.envelope.route
        # message_new
        return
