from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class ProductTemplateListener(Component):
    _name = "edi.product.template.listener"
    _inherit = "base.event.listener"
    _apply_on = ["product.template"]

    def on_record_create_edi(self, recordset):
        edi_route_event_id = self.env.ref(
            "connector_edi_product.route_event_product_template_write"
        )

        edi_route_ids = self.env["edi.route"].search(
            [
                ("action_trigger", "=", "model_event"),
                ("direction", "=", "out"),
                ("model_event_id", "=", edi_route_event_id.id),
            ]
        )

        for route in edi_route_ids:
            for record in recordset:
                route.sudo().send_messages_using_first_match(
                    route.backend_id,
                    record,
                    [
                        ("action_trigger", "=", "model_event"),
                        ("direction", "=", "out"),
                        ("model_event_id", "=", edi_route_event_id.id),
                    ],
                )

    def on_record_write_edi(self, recordset, fields=None):
        edi_route_event_id = self.env.ref(
            "connector_edi_product.route_event_product_template_write"
        )

        for record in recordset:
            edi_product_id = record.edi_product_tmpl_ids

            if not edi_product_id:
                self.on_record_create_edi(record)
                return

            if len(edi_product_id) > 1:
                msg = _(
                    f"Multiple EDI records found for product.template record {record.id}"
                )
                raise UserError(msg)

            self.env["edi.route"].sudo().send_messages_using_first_match(
                edi_product_id.backend_id,
                record,
                [
                    ("action_trigger", "=", "model_event"),
                    ("direction", "=", "out"),
                    ("model_event_id", "=", edi_route_event_id.id),
                ],
            )
