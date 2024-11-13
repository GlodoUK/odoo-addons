from odoo import _, api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_qty_delivered(self):
        res = super()._compute_qty_delivered()
        for line in self.filtered(
            lambda order_line: order_line.product_id.commingled_ok
            and order_line.qty_delivered_method == "stock_move"
        ):
            moves = line.move_ids.filtered(
                lambda m: m.picking_id
                and m.picking_id.state != "cancel"
                and m.state == "done"
            )
            outgoing_moves = moves.filtered(
                lambda m: m.location_dest_id.usage == "customer"
                and (
                    not m.origin_returned_move_id
                    or (m.origin_returned_move_id and m.to_refund)
                )
            )
            returned = all(
                [
                    moves.filtered(
                        lambda m, move=move: m.location_dest_id.usage != "customer"
                        and m.to_refund
                        and m.origin_returned_move_id.id == move.id
                    )
                    for move in outgoing_moves
                ]
            )
            if moves and not returned:
                line.qty_delivered = line.product_uom_qty
            else:
                line.qty_delivered = 0.0

        return res

    @api.onchange(
        "product_id",
        "product_uom_qty",
        "product_uom",
        "warehouse_id",
    )
    def _onchange_product_id_commingle(self):
        if (
            not self.product_id.commingled_ok
            or not self.product_uom_qty
            or not self.product_uom
        ):
            return

        quantity = self.product_uom._compute_quantity(
            self.product_uom_qty,
            self.product_id.uom_id,
        )

        lines = self.product_id._explode_commingled(
            quantity,
            self.order_id.warehouse_id.lot_stock_id,
        )

        if len(lines) > 1:
            return {
                "warning": {
                    "title": "Warning",
                    "message": _("This product will split into %s lines") % len(lines),
                }
            }
