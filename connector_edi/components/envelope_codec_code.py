from odoo.addons.component.core import Component


class EnvelopeCodecCodeComponent(Component):
    _name = "edi.envelope.codec.code"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "codec.code"
    _apply_on = "edi.envelope"

    def open(self, envelope_id, **kwargs):
        with self.env.cr.savepoint():
            self._safe_eval(envelope_id.route_id.codec_code_open, record=envelope_id)

    def enclose(self, message_ids, **kwargs):
        with self.env.cr.savepoint():
            for route_id in message_ids.mapped("envelope_route_id"):
                self._safe_eval(
                    route_id.codec_code_enclose,
                    record=message_ids.filtered(
                        lambda m, route_id=route_id: m.envelope_route_id == route_id
                    ),
                )
