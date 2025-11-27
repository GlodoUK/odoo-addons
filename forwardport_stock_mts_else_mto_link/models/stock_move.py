from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_procurement_values(self):
        res = super()._prepare_procurement_values()
        if (
            self.procure_method in ("make_to_order", "mts_else_mto")
            or (
                self.rule_id.procure_method == "mts_else_mto"
                and self.procure_method not in ("make_to_order", "mts_else_mto")
            )
        ) and not res.get("move_dest_ids"):
            res.update({"move_dest_ids": self})
        return res
