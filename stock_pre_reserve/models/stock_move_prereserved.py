from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockMovePrereserved(models.Model):
    _name = "stock.move.prereserved"
    _description = "Stock Move Reservation - Aids tracking manually linked stock.moves"

    """
    This model is extremely similar to the table stock_move_move_rel.
    However, it's main purpose is to act as a distinction between manually
    created links and links made transfers.
    """

    move_orig_id = fields.Many2one(
        "stock.move",
        required=True,
        index=True,
    )
    move_dest_id = fields.Many2one(
        "stock.move",
        required=True,
        index=True,
    )

    orig_product_id = fields.Many2one(
        related="move_orig_id.product_id",
        store=False,
    )
    dest_product_id = fields.Many2one(
        related="move_dest_id.product_id",
        store=False,
    )

    orig_state = fields.Selection(related="move_orig_id.state", store=False)
    dest_state = fields.Selection(related="move_dest_id.state", store=False)

    orig_product_uom_qty = fields.Float(
        related="move_orig_id.product_uom_qty",
        store=False,
    )
    dest_product_uom_qty = fields.Float(
        related="move_dest_id.product_uom_qty",
        store=False,
    )

    orig_product_uom = fields.Many2one(
        related="move_orig_id.product_uom",
        store=False,
    )
    dest_product_uom = fields.Many2one(
        related="move_dest_id.product_uom",
        store=False,
    )

    orig_picking_id = fields.Many2one(
        related="move_orig_id.picking_id", store=True, index=True
    )

    dest_picking_id = fields.Many2one(
        related="move_dest_id.picking_id", store=True, index=True
    )

    product_uom_qty_reserved = fields.Float(
        help="""Quantity assumed to be taken at time of linking.
This may not be accurate if other links are made/broken"""
    )

    @api.model
    def _link_moves(self, src_move_id, dest_move_id, **kwargs):
        """
        Utility function to help manually link moves
        """

        if not src_move_id or not dest_move_id:
            raise UserError(
                _(
                    "Attempted to link 2 moves together, but either the source"
                    " or the destination was missing"
                )
            )

        if src_move_id.product_uom != dest_move_id.product_uom:
            raise UserError(
                _(
                    "Attempted to link 2 moves together with different UoMs. This "
                    "is not yet supported."
                )
            )

        if src_move_id.product_id != dest_move_id.product_id:
            raise UserError(
                _(
                    "Attempted to link 2 moves together with different products. "
                    "This is not supported"
                )
            )

        if dest_move_id.state in ["done", "cancel", "draft"]:
            raise UserError(_("Move is not in a validate state to link."))

        if kwargs.get("unreserve", False):
            dest_move_id._do_unreserve()

        # XXX: Determine the amount likely to go to the linked move, based on
        # the current links.
        # This does not update, based on other links being made or broken,
        # therefore it will never be 100% accurate.

        src_move_available = src_move_id.product_uom_qty - sum(
            src_move_id.move_dest_ids.mapped(
                lambda c: c.product_uom_qty - c.reserved_availability
            )
        )

        if (
            float_compare(
                src_move_available,
                0.0,
                precision_rounding=src_move_id.product_uom.rounding,
            )
            <= 0
        ):
            raise UserError(
                _("Cannot link moves. There is no available stock on move %s.")
                % (src_move_id)
            )

        dest_move_required = (
            dest_move_id.product_uom_qty - dest_move_id.reserved_availability
        )

        potentially_reserved = 0.0

        if (
            float_compare(
                src_move_available,
                dest_move_required,
                precision_rounding=src_move_id.product_uom.rounding,
            )
            >= 0
        ):
            potentially_reserved = dest_move_required
        else:
            potentially_reserved = src_move_available

        src_move_id.move_dest_ids = [(4, dest_move_id.id, False)]
        self.create(
            {
                "move_dest_id": dest_move_id.id,
                "move_orig_id": src_move_id.id,
                "product_uom_qty_reserved": potentially_reserved,
            }
        )

        dest_move_id.state = "waiting"

    @api.model
    def _unlink_dest_moves(self, move_ids, **kwargs):
        """
        Unlink manually created move_dest_id for given move_ids
        """
        if not move_ids:
            return move_ids

        if kwargs.get("remove_all", False):
            # if remove_all is passed then we kill all connections, not just
            # manual ones
            manual_ids = self.search([("move_orig_id", "in", move_ids.ids)])
            move_ids_to_remove = [(5, 0, 0)]
            moves_to_patch = move_ids.mapped("move_dest_ids")
        else:
            manual_ids = self.search([("move_orig_id", "in", move_ids.ids)])
            moves_to_patch = manual_ids.mapped("move_dest_id")
            move_ids_to_remove = [
                (3, move_id, 0) for move_id in manual_ids.mapped("move_dest_id").ids
            ]

        if move_ids and move_ids_to_remove:
            move_ids.write(
                {
                    "move_dest_ids": move_ids_to_remove,
                }
            )

        move_ids = move_ids.filtered(
            lambda m: m.state not in ["cancel", "done"]  # and m.prereserved_dest_ids
        )  # Re: #1495

        if move_ids:
            move_ids.write(
                {
                    "procure_method": "make_to_stock",
                }
            )
            move_ids._recompute_state()

        moves_to_patch = moves_to_patch.filtered(
            lambda m: m.state not in ["cancel", "done"]
        )

        if moves_to_patch:
            moves_to_patch.write(
                {
                    "procure_method": "make_to_stock",
                }
            )
            moves_to_patch._recompute_state()

        if manual_ids:
            manual_ids.unlink()

        self._recalculate_dest_reserved_qty(move_ids)

        return move_ids

    @api.model
    def _unlink_orig_moves(self, move_ids, **kwargs):
        """
        Unlink manually created move_orig_id for given move_ids
        """
        if not move_ids:
            return move_ids

        if kwargs.get("remove_all", False):
            # if remove_all is passed then we kill all connections, not just
            # manual ones
            move_ids_to_remove = [(5, 0, 0)]
            moves_to_recalc = move_ids.mapped("move_orig_ids")
            manual_ids = self.search([("move_dest_id", "in", move_ids.ids)])

        else:
            manual_ids = self.search([("move_dest_id", "in", move_ids.ids)])
            moves_to_recalc = manual_ids.mapped("move_orig_id")
            move_ids_to_remove = [
                (3, move_id, 0) for move_id in manual_ids.mapped("move_orig_id").ids
            ]
            manual_ids.unlink()

        if move_ids and move_ids_to_remove:
            move_ids.write(
                {
                    "move_orig_ids": move_ids_to_remove,
                }
            )

        move_ids = move_ids.filtered(
            lambda m: m.state not in ["cancel", "done"]
        )  # Re: #1495

        if move_ids:
            move_ids.write(
                {
                    "procure_method": "make_to_stock",
                }
            )
            move_ids._recompute_state()

        if manual_ids:
            manual_ids.unlink()

        if moves_to_recalc:
            self._recalculate_dest_reserved_qty(moves_to_recalc)

        return move_ids

    @api.model
    def _recalculate_dest_reserved_qty(self, src_move_ids):
        for src_move_id in src_move_ids:
            src_move_available = src_move_id.product_uom_qty

            for dest_move_id in src_move_id.move_dest_ids:
                qty = dest_move_id.product_uom_qty - dest_move_id.reserved_availability

                reserved = 0

                if src_move_available > 0 and qty > 0:
                    if qty >= src_move_available:
                        src_move_available = 0
                        reserved = src_move_available
                    else:
                        reserved = qty
                        src_move_available = src_move_available - qty

                pre_reserved = self.search(
                    [
                        ("move_orig_id", "=", src_move_id.id),
                        ("move_dest_id", "=", dest_move_id.id),
                    ]
                )
                if pre_reserved:
                    pre_reserved.write({"product_uom_qty_reserved": reserved})
