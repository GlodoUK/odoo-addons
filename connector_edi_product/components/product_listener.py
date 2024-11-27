from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class ProductProductListener(Component):
    _name = "edi.product.product.listener"
    _inherit = "base.event.listener"
    _apply_on = ["product.product"]

    def on_record_write_edi(self, records, fields=None):
        for record in records:
            edi_product_id = record.edi_product_ids

            if not edi_product_id:
                self.on_record_create_edi(record)
                return

            if len(edi_product_id) > 1:
                raise UserError(
                    _("Multiple EDI records found for product.product record %s")
                    % record.id
                )

            self.env["edi.route"].sudo().send_messages_using_first_match(
                edi_product_id.backend_id,
                record,
                [
                    ("action_trigger", "=", "model_event"),
                    (
                        "model_event_id",
                        "=",
                        self.env.ref(
                            "connector_edi_product.route_event_product_write"
                        ).id,
                    ),
                    ("direction", "=", "out"),
                ],
            )

    def on_record_create_edi(self, records):
        routes = self.env["edi.route"].search(
            [
                ("action_trigger", "=", "model_event"),
                (
                    "model_event_id",
                    "=",
                    self.env.ref("connector_edi_product.route_event_product_write").id,
                ),
                ("direction", "=", "out"),
            ]
        )
        if not routes:
            return
        for route in routes:
            for record in records:
                route.sudo().send_messages_using_first_match(
                    route.backend_id,
                    record,
                    [
                        ("action_trigger", "=", "model_event"),
                        (
                            "model_event_id",
                            "=",
                            self.env.ref(
                                "connector_edi_product.route_event_product_write"
                            ).id,
                        ),
                        ("direction", "=", "out"),
                    ],
                )


class ProductTemplateListener(Component):
    _name = "edi.product.template.listener"
    _inherit = "base.event.listener"
    _apply_on = ["product.template"]

    def on_record_write_edi(self, records, fields=None):
        for record in records:
            if not record.edi_product_tmpl_ids:
                self.on_record_create_edi(record)
                return

            for binding_id in record.edi_product_tmpl_ids:
                self.env["edi.route"].sudo().send_messages_using_first_match(
                    binding_id.backend_id,
                    record,
                    [
                        ("action_trigger", "=", "model_event"),
                        (
                            "model_event_id",
                            "=",
                            self.env.ref(
                                "connector_edi_product.route_event_product_template_write"
                            ).id,
                        ),
                        ("direction", "=", "out"),
                    ],
                )

    def on_record_create_edi(self, records):
        for backend_id in self.env["edi.backend"].search([]):
            for record in records:
                self.env["edi.route"].sudo().send_messages_using_first_match(
                    backend_id,
                    record,
                    [
                        ("action_trigger", "=", "model_event"),
                        (
                            "model_event_id",
                            "=",
                            self.env.ref(
                                "connector_edi_product.route_event_product_template_create"
                            ).id,
                        ),
                        ("direction", "=", "out"),
                    ],
                )
