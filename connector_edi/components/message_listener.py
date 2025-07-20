from odoo.addons.component.core import Component


class EdiMessageListener(Component):
    _name = "edi.message.listener"
    _inherit = "base.event.listener"
    _apply_on = ["edi.message"]

    def no_connector_export(self, record):
        # FIXME: duplicated because we've inherited off base.event.listener rather than
        # base.connector.listener.
        return record.env.context.get("no_connector_export") or record.env.context.get(
            "connector_no_export"
        )

    def on_pending(self, record):
        if self.no_connector_export(record):
            return

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
