from odoo.addons.component.core import Component


class StockPickingListener(Component):
    _name = "edi.stock.picking.listener"
    _inherit = "base.event.listener"
    _apply_on = ["stock.picking"]

    def no_connector_export(self, record):
        # FIXME: duplicated because we've inherited off base.event.listener rather than
        # base.connector.listener.
        return record.env.context.get("no_connector_export") or record.env.context.get(
            "connector_no_export"
        )

    def on_picking_in_cancel(self, record, completed=False):
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
                            "connector_edi_stock.route_event_stock_picking_in_cancel"
                        ).id,
                    ),
                    ("direction", "=", "out"),
                ],
            )

    def on_picking_out_cancel(self, record, completed=False):
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
                            "connector_edi_stock.route_event_stock_picking_out_cancel"
                        ).id,
                    ),
                    ("direction", "=", "out"),
                ],
            )

    def on_picking_assigned(self, record, completed=False):
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
                            "connector_edi_stock.route_event_stock_picking_assigned"
                        ).id,
                    ),
                    ("direction", "=", "out"),
                ],
            )

    def on_picking_unreserved(self, record, completed=False):
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
                            "connector_edi_stock.route_event_stock_picking_unreserved"
                        ).id,
                    ),
                    ("direction", "=", "out"),
                ],
            )


class StockMoveListener(Component):
    _name = "edi.stock.move.listener"
    _inherit = "base.event.listener"
    _apply_on = ["stock.move"]

    def no_connector_export(self, record):
        # FIXME: duplicated because we've inherited off base.event.listener rather than
        # base.connector.listener.
        return record.env.context.get("no_connector_export") or record.env.context.get(
            "connector_no_export"
        )

    def on_move_done(self, record, completed=False):
        if self.no_connector_export(record):
            return

        route_domain = [
            ("action_trigger", "=", "model_event"),
            (
                "model_event_id",
                "=",
                self.env.ref("connector_edi_stock.route_event_stock_move_done").id,
            ),
            ("direction", "=", "out"),
        ]
        applicable_routes = self.env["edi.route"].sudo().search(route_domain)
        for route in applicable_routes:
            route.send_messages_using_first_match(
                route.backend_id, record, route_domain
            )

    def on_move_reserved_changed(self, record, completed=False):
        if self.no_connector_export(record):
            return

        route_domain = [
            ("action_trigger", "=", "model_event"),
            (
                "model_event_id",
                "=",
                self.env.ref(
                    "connector_edi_stock.route_event_stock_move_reserved_changed"
                ).id,
            ),
            ("direction", "=", "out"),
        ]
        applicable_routes = self.env["edi.route"].sudo().search(route_domain)
        for route in applicable_routes:
            route.send_messages_using_first_match(
                route.backend_id, record, route_domain
            )
