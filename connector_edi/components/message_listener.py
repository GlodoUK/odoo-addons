from odoo.addons.component.core import Component


class EdiMessageListener(Component):
    _name = "edi.message.listener"
    _inherit = "base.event.listener"
    _apply_on = ["edi.message"]

    def on_pending(self, record):
        if record.direction == "in" and record.state == "pending":
            opts = {}
            if record.message_route_id:
                opts = record.message_route_id._with_delay_options()
            record.with_delay(**opts)._read_message()
        elif (
            record.direction == "out"
            and record.state == "pending"
            and record.envelope_route_id.protocol_out_trigger == "none"
        ):
            opts = {}
            if record.envelope_route_id:
                opts = record.envelope_route_id._with_delay_options(
                    usage="enclose_messages"
                )
            self.env["edi.envelope"].with_delay(**opts)._enclose_messages(
                record.envelope_route_id,
                record,
            )
