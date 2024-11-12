from odoo import api, fields, models
from odoo.tools import OrderedSet


class StockMove(models.Model):
    _inherit = "stock.move"

    commingled_original_product_id = fields.Many2one(
        "product.product",
        "Commingled Product",
    )

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields.append("commingled_original_product_id")
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        keys_sorted = super()._prepare_merge_move_sort_method(move)
        keys_sorted.append(move.commingled_original_product_id.id)
        return keys_sorted

    def _action_confirm(self, merge=True, merge_into=False):
        moves = self._action_commingled()

        return super(StockMove, moves)._action_confirm(
            merge=merge, merge_into=merge_into
        )

    def _skip_action_commingled(self):
        self.ensure_one()
        return not self.product_id.commingled_ok or not self.picking_type_id

    def _action_commingled(self):
        # Explodes commingled stock
        #
        # In order to explode a move, we must have a picking_type_id on that
        # move because otherwise the move won't be assigned to a picking and it
        # would be weird to explode a move into several if they aren't
        # all grouped in the same picking.

        moves_ids_to_return = OrderedSet()
        moves_ids_to_unlink = OrderedSet()
        equiv_moves_vals_list = []
        for move in self:
            if move._skip_action_commingled():
                moves_ids_to_return.add(move.id)
                continue

            lines = move.product_id._explode_commingled(
                move.product_uom_qty,
                move.location_id,
            )
            for bom_line, line_data in lines:
                qty_done = 0
                if move.picking_id.immediate_transfer:
                    qty_done = line_data.get("qty")

                equiv_moves_vals_list += move._generate_move_commingled(
                    bom_line, line_data, qty_done
                )
            # delete the move with original product which is not relevant anymore
            moves_ids_to_unlink.add(move.id)

        self.env["stock.move"].browse(moves_ids_to_unlink).sudo().unlink()
        if equiv_moves_vals_list:
            equivalent_moves = self.env["stock.move"].create(equiv_moves_vals_list)
            equivalent_moves._adjust_procure_method()
            # support commingled within commingled
            moves_ids_to_return |= equivalent_moves._action_commingled().ids
        return self.env["stock.move"].browse(moves_ids_to_return)

    def _prepare_commingled_move_values(self, bom_line, line_data, quantity_done):
        return {
            "picking_id": self.picking_id.id if self.picking_id else False,
            "product_id": bom_line.product_id.id,
            "product_uom": bom_line.product_id.uom_id.id,
            "product_uom_qty": line_data.get("qty"),
            "state": "draft",
            "name": self.name,
            "quantity_done": quantity_done,
            "picking_type_id": self.picking_type_id.id,
            "commingled_original_product_id": (
                self.commingled_original_product_id
                if self.commingled_original_product_id.id
                else self.product_id.id
            ),
        }

    def _generate_move_commingled(self, bom_line, line_data, quantity_done=None):
        vals = []
        if bom_line.product_id.type in ["product", "consu"]:
            vals = self.copy_data(
                default=self._prepare_commingled_move_values(
                    bom_line, line_data, quantity_done
                )
            )
            if self.state == "assigned":
                vals["state"] = "assigned"
        return vals
