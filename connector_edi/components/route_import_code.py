from odoo.addons.component.core import Component


class EdiRouteCodeImporterComponent(Component):
    _name = "edi.route.code.importer"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "import.code"
    _apply_on = "edi.envelope"

    def run(self, route_id, **kwargs):
        # Sample usage, create an edi.backend where code_in is populated as
        # follows:
        #
        # e = env['edi.envelope'].create({
        #   'route_id': route_id.id,
        #   'backend_id': backend.id,
        #   'body': 'test!',
        #   'external_id': 'test',
        #   'direction': 'in'
        # })
        #
        # e.action_pending()

        kwargs.update(
            {
                "route_id": route_id,
            }
        )

        self._safe_eval(route_id.code_in, **kwargs)
