from odoo.addons.component.core import Component


class EdiMessageListener(Component):
    _name = "edi.message.listener"
    _inherit = "base.event.listener"
    _apply_on = ["edi.message"]

    def on_pending(self, record):
        if record.direction == "in" and record.state == "pending":
            record.with_delay()._read_message()
        elif (
            record.direction == "out"
            and record.state == "pending"
            and record.envelope_route_id.protocol_out_trigger == "none"
        ):
            self.env["edi.envelope"].with_delay()._enclose_messages(
                record.envelope_route_id,
                record,
            )
