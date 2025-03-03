from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _skip_action_commingled(self):
        res = super()._skip_action_commingled()

        return res or (
            self.production_id and self.production_id.product_id == self.product_id
        )

    def _action_commingled(self):
        before_commingling = set(self.ids)
        # support phantom kits within commingled
        moves = super()._action_commingled()
        if before_commingling != set(moves.ids):
            moves = moves.action_explode()
        return moves

    def action_explode(self):
        before_explosion = set(self.ids)
        moves = super().action_explode()
        if before_explosion != set(moves.ids) and moves.filtered(
            lambda m: not m._skip_action_commingled()
        ):
            # support commingled within phantom kits
            moves = moves._action_commingled()
        return moves
