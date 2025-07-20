from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class AccountInvoiceListener(Component):
    _name = "edi.sale.account.invoice.listener"
    _inherit = "base.event.listener"
    _apply_on = ["account.move"]

    def no_connector_export(self, record):
        # FIXME: duplicated because we've inherited off base.event.listener rather than
        # base.connector.listener.
        return record.env.context.get("no_connector_export") or record.env.context.get(
            "connector_no_export"
        )

    def on_out_invoice_open(self, record):
        if self.no_connector_export(record):
            return

        edi_sale_id = record.sudo().mapped(
            "invoice_line_ids.sale_line_ids.order_id.edi_sale_order_ids"
        )

        if not edi_sale_id:
            return

        if len(edi_sale_id) > 1:
            raise UserError(_("Connector does not support consolidated invoices"))

        self.env["edi.route"].sudo().send_messages_using_first_match(
            edi_sale_id.backend_id,
            record,
            [
                ("action_trigger", "=", "model_event"),
                (
                    "model_event_id",
                    "=",
                    self.env.ref("connector_edi_sale.route_event_invoice_out_open").id,
                ),
                ("direction", "=", "out"),
            ],
        )
