from odoo.addons.component.core import Component


class EdiMessageListener(Component):
    _name = "edi.message.listener"
    _inherit = "base.event.listener"
    _apply_on = ["edi.message"]

    def on_pending(self, message_id):
        if message_id.direction == "in" and message_id.state == "pending":
            opts = {}
            if message_id.message_route_id:
                opts = message_id.message_route_id._with_delay_options()
            message_id.with_delay(**opts)._read_message()
        elif (
            message_id.direction == "out"
            and message_id.state == "pending"
            and message_id.envelope_route_id.protocol_out_trigger == "none"
        ):
            opts = {}
            if message_id.envelope_route_id:
                opts = message_id.envelope_route_id._with_delay_options(
                    usage="enclose_messages"
                )
            self.env["edi.envelope"].with_delay(**opts)._enclose_messages(
                message_id.envelope_route_id,
                message_id,
            )
