from odoo.addons.component.core import Component


class StockPickingListener(Component):
    _name = "edi.stock.picking.listener"
    _inherit = "base.event.listener"
    _apply_on = ["stock.picking"]

    def on_picking_in_cancel(self, record, completed=False):
        route_event_in_cancel = self.env.ref(
            "connector_edi_stock.route_event_stock_picking_in_cancel"
        )

        backend_ids = record.sudo().sale_id.mapped("edi_sale_order_ids.backend_id")

        for backend_id in backend_ids:
            self.env["edi.route"].sudo().send_messages_using_first_match(
                backend_id,
                record,
                [
                    ("action_trigger", "=", "model_event"),
                    ("direction", "=", "out"),
                    ("model_event_id", "=", route_event_in_cancel.id),
                ],
            )

    def on_picking_out_cancel(self, record, completed=False):
        route_event_out_cancel = self.env.ref(
            "connector_edi_stock.route_event_stock_picking_out_cancel"
        )

        backend_ids = record.sudo().sale_id.mapped("edi_sale_order_ids.backend_id")

        for backend_id in backend_ids:
            self.env["edi.route"].sudo().send_messages_using_first_match(
                backend_id,
                record,
                [
                    ("action_trigger", "=", "model_event"),
                    ("direction", "=", "out"),
                    ("model_event_id", "=", route_event_out_cancel.id),
                ],
            )

    def on_picking_assigned(self, record, completed=False):
        route_event_assigned = self.env.ref(
            "connector_edi_stock.route_event_stock_picking_assigned"
        )

        backend_ids = record.sudo().sale_id.mapped("edi_sale_order_ids.backend_id")

        for backend_id in backend_ids:
            self.env["edi.route"].sudo().send_messages_using_first_match(
                backend_id,
                record,
                [
                    ("action_trigger", "=", "model_event"),
                    ("direction", "=", "out"),
                    ("model_event_id", "=", route_event_assigned.id),
                ],
            )

    def on_picking_unreserved(self, record, completed=False):
        route_event_unreserved = self.env.ref(
            "connector_edi_stock.route_event_stock_picking_unreserved"
        )

        backend_ids = record.sudo().sale_id.mapped("edi_sale_order_ids.backend_id")

        for backend_id in backend_ids:
            self.env["edi.route"].sudo().send_messages_using_first_match(
                backend_id,
                record,
                [
                    ("action_trigger", "=", "model_event"),
                    ("direction", "=", "out"),
                    ("model_event_id", "=", route_event_unreserved.id),
                ],
            )


class StockMoveListener(Component):
    _name = "edi.stock.move.listener"
    _inherit = "base.event.listener"
    _apply_on = ["stock.move"]

    def on_move_done(self, record, completed=False):
        route_event_done = self.env.ref(
            "connector_edi_stock.route_event_stock_move_done"
        )

        route_domain = [
            ("action_trigger", "=", "model_event"),
            ("direction", "=", "out"),
            ("model_event_id", "=", route_event_done.id),
        ]

        applicable_route_ids = self.env["edi.route"].sudo().search(route_domain)

        for route in applicable_route_ids:
            route.send_messages_using_first_match(
                route.backend_id,
                record,
                route_domain,
            )

    def on_move_reserved_changed(self, record, completed=False):
        route_event_changed = self.env.ref(
            "connector_edi_stock.route_event_stock_move_reserved_changed"
        )

        route_domain = [
            ("action_trigger", "=", "model_event"),
            ("direction", "=", "out"),
            ("model_event_id", "=", route_event_changed.id),
        ]

        applicable_route_ids = self.env["edi.route"].sudo().search(route_domain)

        for route in applicable_route_ids:
            route.send_messages_using_first_match(
                route.backend_id,
                record,
                route_domain,
            )
