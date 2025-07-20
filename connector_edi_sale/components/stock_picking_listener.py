from odoo.addons.component.core import Component


class StockPickingListener(Component):
    _name = "edi.sale.stock.picking.listener"
    _inherit = "base.event.listener"
    _apply_on = ["stock.picking"]

    def no_connector_export(self, record):
        # FIXME: duplicated because we've inherited off base.event.listener rather than
        # base.connector.listener.
        return record.env.context.get("no_connector_export") or record.env.context.get(
            "connector_no_export"
        )

    def on_picking_out_done(self, record, completed):
        if self.no_connector_export(record):
            return

        for backend_id in record.sudo().sale_id.mapped("edi_sale_order_ids.backend_id"):
            self.env["edi.route"].sudo().send_messages_using_first_match(
                backend_id,
                record,
                [
                    ("action_trigger", "=", "model_event"),
                    (
                        "model_event_id",
                        "=",
                        self.env.ref(
                            "connector_edi_sale.route_event_stock_picking_done"
                        ).id,
                    ),
                    ("direction", "=", "out"),
                ],
            )
