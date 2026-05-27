from odoo import models
from odoo.exceptions import UserError

MERGE_FORBIDDEN_STATES = ("waiting", "done", "cancel")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _ensure_can_merge(self):
        """Raise UserError if self cannot be safely merged."""
        if len(self) < 2:
            raise UserError(self.env._("Please select at least two pickings to merge."))

        forbidden = self.filtered(lambda p: p.state in MERGE_FORBIDDEN_STATES)
        if forbidden:
            raise UserError(
                self.env._(
                    "The following pickings cannot be merged because of their state: "
                    " %(names)s",
                    names=", ".join(forbidden.mapped("name")),
                )
            )

        if len(self.picking_type_id) > 1:
            raise UserError(
                self.env._(
                    "All pickings must have the same operation type to be merged."
                )
            )

        if not self.picking_type_id.allow_merge:
            raise UserError(
                self.env._(
                    "Merging is not enabled for operation type '%(ty)s'. "
                    "Enable 'Allow Merge' on the operation type to proceed.",
                    ty=self.picking_type_id.name,
                )
            )

        if len(self.location_id) > 1:
            raise UserError(
                self.env._(
                    "All pickings must have the same source location to be merged."
                )
            )

        if len(self.location_dest_id) > 1:
            raise UserError(
                self.env._(
                    "All pickings must have the same destination location to be merged."
                )
            )

        if (
            len({p.partner_id.id for p in self}) > 1
        ):  # XXX: Don't optimise! Mapped removes False-y values.
            raise UserError(
                self.env._("All pickings must have the same partner to be merged.")
            )

    def _action_merge(self, target_picking_id=None):
        """Merge self (a recordset of stock.pickings) into a single picking.

        All moves are reassigned to the picking with the lowest ID; the
        remaining empty pickings are cancelled.
        """
        self._ensure_can_merge()

        if not target_picking_id:
            target_picking_id = self.sorted("id")[0]
        sources = self - target_picking_id

        source_moves = {
            source: [
                (
                    move.product_id.display_name,
                    move.product_uom_qty,
                    move.product_uom.name,
                )
                for move in source.move_ids
            ]
            for source in sources
        }

        merged_origins = ", ".join(filter(None, self.mapped("origin")))
        sources.move_ids.write({"picking_id": target_picking_id.id})
        sources.action_cancel()

        if merged_origins:
            target_picking_id.origin = merged_origins

        target_picking_id.message_post_with_source(
            "stock_picking_merge.stock_picking_merge_target_message",
            render_values={"sources": list(source_moves.items())},
            subtype_xmlid="mail.mt_note",
        )
        for source, moves in source_moves.items():
            source.message_post_with_source(
                "stock_picking_merge.stock_picking_merge_source_message",
                render_values={"target": target_picking_id, "moves": moves},
                subtype_xmlid="mail.mt_note",
            )

        return target_picking_id
