from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class ProductProductListener(Component):
    _name = "edi.product.product.listener"
    _inherit = "base.event.listener"
    _apply_on = ["product.product"]

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

    def on_record_write_edi(self, product_ids, fields=None):
        edi_route_event_id = self.env.ref(
            "connector_edi_product.route_event_product_write"
        )

        for product in product_ids:
            if not product.edi_product_ids:
                self.on_record_create_edi(product)
                return

            if len(product.edi_product_ids) > 1:
                msg = _(
                    f"Multiple EDI records found for product.product record {product.name}"
                )
                raise UserError(msg)

            self.env["edi.route"].sudo().send_messages_using_first_match(
                product.edi_product_ids.backend_id,
                product,
                [
                    ("action_trigger", "=", "model_event"),
                    ("direction", "=", "out"),
                    ("model_event_id", "=", edi_route_event_id.id),
                ],
            )
