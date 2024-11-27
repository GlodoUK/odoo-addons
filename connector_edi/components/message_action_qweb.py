from lxml import etree

from odoo.addons.component.core import Component


class EdiMessageActionCodeComponent(Component):
    _name = "edi.message.action.qweb"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "action.qweb"
    _apply_on = "edi.message"

    def run_read(self, message_id, **kwargs):
        raise NotImplementedError()

    def run_write(self, route_id, **kwargs):
        with self.env.cr.savepoint():
            qweb_etree = etree.fromstring(route_id.qweb_arch)
            values = self._get_default_eval_context()
            values.update(
                {
                    "route_id": route_id,
                }
            )

            data = self.env["ir.qweb"]._render(qweb_etree, values=values)

            seq = False

            if self.backend_record.sudo().message_sequence:
                seq = self.backend_record.sudo().message_sequence._next()

            msg = self.env["edi.message"].create(
                {
                    "message_route_id": route_id.id,
                    "direction": route_id.direction,
                    "body": str(data),
                    "backend_id": self.backend_record.id,
                    "external_id": seq,
                }
            )

            msg.action_pending()
