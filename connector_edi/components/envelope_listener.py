from odoo.addons.component.core import Component


class EdiEnvelopeListener(Component):
    _name = "edi.envelope.listener"
    _inherit = "base.event.listener"
    _apply_on = ["edi.envelope"]

    def on_pending(self, record):
        if record.direction == "in":
            opts = {}
            if record.route_id:
                opts = record.route_id._with_delay_options(usage="open_messages")
            record.with_delay(**opts)._open_messages()
        elif (
            record.direction == "out" and record.route_id.protocol_out_trigger == "none"
        ):
            opts = {}
            if record.route_id:
                opts = record.route_id._with_delay_options()
            record.with_delay(**opts)._send_envelopes()
