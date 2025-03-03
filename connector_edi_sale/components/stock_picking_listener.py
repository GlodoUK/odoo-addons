from odoo.addons.component.core import Component


class StockPickingListener(Component):
    _name = "edi.sale.stock.picking.listener"
    _inherit = "base.event.listener"
    _apply_on = ["stock.picking"]

    def on_picking_out_done(self, record, completed):
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
