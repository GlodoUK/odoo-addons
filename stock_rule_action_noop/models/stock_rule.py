from odoo import api, fields, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    action = fields.Selection(
        selection_add=[("noop", "No-Operation")], ondelete={"noop": "cascade"}
    )

    @api.model
    def _run_noop(self, procurements):
        # This is a no-op route used to delegate buying to a third party system.
        # i.e. when it hits this method it does nothing.

        for procurement, _rule in procurements:
            moves = procurement.values.get("move_dest_ids")
            # We want to force the move procure_method to make_to_stock, otherwise we'll
            # have stuck products (i.e. if they were set to make_to_order, they'll
            # forever be waiting)
            if moves:
                moves.write({"procure_method": "make_to_stock"})
                moves._recompute_state()
