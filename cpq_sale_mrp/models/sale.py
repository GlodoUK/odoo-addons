from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_qty_procurement(self, previous_product_uom_qty=False):
        self.ensure_one()
        # Specific case when we change the qty on a SO for a CPQ phantom product.
        # We don't try to be too smart and keep a simple approach: we compare the
        # quantity before and after update, and return the difference.
        # We don't take into account what was already sent, or any other
        # case.
        #
        # Since CPQ Dynamic BoMs can be highly configurable, calculating
        # differences can be complex and non-sensical in some tested
        # circumstances.
        #
        # We are also out of time to deliver, therefore this needs to suffice
        # for the moment.
        bom = (
            self.env["cpq.dynamic.bom"]
            .sudo()
            .search(
                [
                    ("product_tmpl_id", "=", self.product_id.product_tmpl_id.id),
                    ("type", "=", "phantom"),
                ]
            )
        )
        if bom and previous_product_uom_qty:
            return previous_product_uom_qty.get(self.id, 0.0)
        return super()._get_qty_procurement(
            previous_product_uom_qty=previous_product_uom_qty
        )

    def _compute_qty_delivered(self):
        res = super()._compute_qty_delivered()
        for line in self:
            if line.qty_delivered_method == "stock_move" and line.product_id.cpq_ok:
                # In the case of a kit cpq.dynamic.bom, we need to check if all
                # components are shipped.
                # Since the BOM might  have changed, especially on a dynamic BoM,
                # we currently do not compute the quantities but verify the move state.
                #
                # Please see the above notes about my justification for this,
                # for the moment.
                bom = (
                    self.env["cpq.dynamic.bom"]
                    .sudo()
                    .search(
                        [
                            (
                                "product_tmpl_id",
                                "=",
                                line.product_id.product_tmpl_id.id,
                            ),
                            ("type", "=", "phantom"),
                        ]
                    )
                )
                if bom:
                    # bom_delivered
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
                    bom_returned = all(
                        [
                            moves.filtered(
                                lambda m, move=move: m.location_dest_id.usage
                                != "customer"
                                and m.to_refund
                                and m.origin_returned_move_id.id == move.id
                            )
                            for move in outgoing_moves
                        ]
                    )
                    if moves and not bom_returned:
                        line.qty_delivered = (
                            line.qty_delivered_manual or line.product_uom_qty
                        )
                    else:
                        line.qty_delivered = 0.0
        return res
