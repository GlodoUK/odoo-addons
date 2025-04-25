from odoo.addons.component.core import Component


class StockPickingListener(Component):
    _name = "edi.sale.stock.picking.listener"
    _inherit = "base.event.listener"
    _apply_on = ["stock.picking"]

    # XXX : Can the completed parameter be removed?
    def on_picking_out_done(self, picking_id, completed):
        backend_ids = picking_id.sudo().sale_id.mapped("edi_sale_order_ids.backend_id")

        event_id = self.env.ref("connector_edi_sale.route_event_stock_picking_done")

        for backend in backend_ids:
            self.env["edi.route"].sudo().send_messages_using_first_match(
                backend,
                picking_id,
                [
                    ("action_trigger", "=", "model_event"),
                    ("direction", "=", "out"),
                    ("model_event_id", "=", event_id.id),
                ],
            )
