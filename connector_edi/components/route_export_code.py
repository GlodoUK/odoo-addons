from odoo.addons.component.core import Component


class EdiRouteCodeExporterComponent(Component):
    _name = "edi.route.code.exporter"
    _inherit = ["base.exporter", "edi.connector"]
    _usage = "export.code"
    _apply_on = "edi.envelope"

    def run(self, route_id, **kwargs):
        envelope_ids = kwargs.get("envelope_ids", None)
        if not envelope_ids:
            envelope_ids = self.env["edi.envelope"].search(
                [
                    ("route_id", "=", route_id.id),
                    ("direction", "=", "out"),
                    ("state", "=", "pending"),
                ]
            )

        for envelope_id in envelope_ids:
            self._run(route_id, envelope_id)

    def _run(self, route_id, envelope_id):
        self._safe_eval(
            route_id.code_out,
            record=envelope_id,
            route_id=route_id,
        )
