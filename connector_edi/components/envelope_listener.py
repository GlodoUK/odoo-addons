from odoo.addons.component.core import Component


class EdiEnvelopeListener(Component):
    _name = "edi.envelope.listener"
    _inherit = "base.event.listener"
    _apply_on = ["edi.envelope"]

    def on_pending(self, record):
        if record.direction == "in":
            record.with_delay()._open_messages()
        elif (
            record.direction == "out" and record.route_id.protocol_out_trigger == "none"
        ):
            record.with_delay()._send_envelopes()
