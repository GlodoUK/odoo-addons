from odoo.addons.component.core import Component


class EdiEnvelopeListener(Component):
    _name = "edi.envelope.listener"
    _inherit = "base.event.listener"
    _apply_on = ["edi.envelope"]

    def on_pending(self, envelope_id):
        if envelope_id.direction == "in":
            opts = {}

            if envelope_id.route_id:
                opts = envelope_id.route_id._with_delay_options(usage="open_messages")  # noqa: E501

            envelope_id.with_delay(**opts)._open_messages()

        elif (
            envelope_id.direction == "out"
            and envelope_id.route_id.protocol_out_trigger == "none"
        ):
            opts = {}

            if envelope_id.route_id:
                opts = envelope_id.route_id._with_delay_options()

            envelope_id.with_delay(**opts)._send_envelopes()
