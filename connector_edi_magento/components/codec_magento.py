import json

from odoo.addons.component.core import Component


class CodecMagentoComponent(Component):
    _name = "edi.envelope.codec.magento"
    _inherit = "edi.envelope.codec.simple"
    _usage = "codec.magento"
    _apply_on = "edi.envelope"

    def open(self, envelope_id, **kwargs):
        with self.env.cr.savepoint():
            content = json.loads(envelope_id.body)
            for item in content.get("items", []):
                item_id = str(item.get("increment_id", ""))
                external_id = envelope_id.external_id
                if item_id:
                    external_id += "-" + item_id
                else:
                    external_id += "-" + str(item.get("id", ""))
                m = self.env["edi.message"].create(
                    {
                        "envelope_id": envelope_id.id,
                        "envelope_route_id": envelope_id.route_id.id,
                        "body": json.dumps(item),
                        "external_id": external_id,
                        "direction": "in",
                        "backend_id": self.backend_record.id,
                        "content_filename": external_id + ".json",
                    }
                )
                m.action_pending()
