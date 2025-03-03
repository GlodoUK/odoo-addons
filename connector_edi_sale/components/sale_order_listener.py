from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class SaleOrderListener(Component):
    _name = "edi.sale.sale.order.listener"
    _inherit = "base.event.listener"
    _apply_on = ["sale.order"]

    def on_confirm(self, record):
        edi_sale_ids = record.sudo().mapped('edi_sale_order_ids')

        if not edi_sale_ids:
            return

        for edi_sale_id in edi_sale_ids:
            self.env["edi.route"].sudo().send_messages_using_first_match(
                edi_sale_id.backend_id,
                record,
                [
                    ("action_trigger", "=", "model_event"),
                    (
                        "model_event_id",
                        "=",
                        self.env.ref("connector_edi_sale.route_event_sale_on_confirm").id,
                    ),
                    ("direction", "=", "out"),
                ],
            )
