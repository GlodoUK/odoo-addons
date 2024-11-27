from odoo.addons.component.core import Component


class CodecSimpleComponent(Component):
    _name = "edi.envelope.codec.simple"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "codec.simple"
    _apply_on = "edi.envelope"

    def open(self, envelope_id, **kwargs):
        with self.env.cr.savepoint():
            m = self.env["edi.message"].create(
                {
                    "envelope_id": envelope_id.id,
                    "envelope_route_id": envelope_id.route_id.id,
                    "body": envelope_id.body,
                    "external_id": envelope_id.external_id,
                    "direction": "in",
                    "backend_id": self.backend_record.id,
                }
            )
            m.action_pending()

    def enclose(self, message_ids, **kwargs):
        with self.env.cr.savepoint():
            for message_id in message_ids:
                envelope_id = self.env["edi.envelope"].create(
                    {
                        "route_id": message_id.envelope_route_id.id,
                        "body": message_id.body,
                        "external_id": message_id.id,
                        "direction": "out",
                        "backend_id": self.backend_record.id,
                        "type": message_id.type,
                    }
                )

                message_id.envelope_id = envelope_id
                envelope_id.action_pending()
