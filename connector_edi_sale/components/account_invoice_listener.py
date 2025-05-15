from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class AccountInvoiceListener(Component):
    _name = "edi.sale.account.invoice.listener"
    _inherit = "base.event.listener"
    _apply_on = ["account.move"]

    def on_out_invoice_open(self, move_id):
        edi_sale_ids = move_id.sudo().mapped(
            "invoice_line_ids.sale_line_ids.order_id.edi_sale_order_ids"
        )

        if not edi_sale_ids:
            return

        if len(edi_sale_ids) > 1:
            msg = _("The connector does not support consolidated invoices.")
            raise UserError(msg)

        event_id = self.env.ref(
            "connector_edi_sale.route_event_invoice_out_open",
        )

        self.env["edi.route"].sudo().send_messages_using_first_match(
            edi_sale_ids.backend_id,
            move_id,
            [
                ("action_trigger", "=", "model_event"),
                ("direction", "=", "out"),
                ("model_event_id", "=", event_id.id),
            ],
        )
