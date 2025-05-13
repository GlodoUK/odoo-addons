from odoo.addons.component.core import Component


class CodecSimpleComponent(Component):
    _name = "edi.envelope.codec.simple"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "codec.simple"
    _apply_on = "edi.envelope"

    def enclose(self, message_ids, **kwargs):
        with self.env.cr.savepoint():
            for message in message_ids:
                envelope_id = self.env["edi.envelope"].create(
                    {
                        "body": message.body,
                        "direction": "out",
                        "type": message.type,
                        "backend_id": self.backend_record.id,
                        "external_id": message.id,
                        "route_id": message.envelope_route_id.id,
                    }
                )

                message.envelope_id = envelope_id

                envelope_id.action_pending()

    def open(self, envelope_id, **kwargs):
        with self.env.cr.savepoint():
            message_id = self.env["edi.message"].create(
                {
                    "body": envelope_id.body,
                    "direction": "in",
                    "backend_id": self.backend_record.id,
                    "envelope_id": envelope_id.id,
                    "envelope_route_id": envelope_id.route_id.id,
                    "external_id": envelope_id.external_id,
                }
            )

            message_id.action_pending()
