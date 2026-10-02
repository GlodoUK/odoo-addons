from odoo import models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def action_apply_inventory_with_reason(self):
        """Open the inventory reason wizard for these quants instead of
        applying them straight away with the default reason."""
        ctx = dict(self.env.context, default_quant_ids=self.ids)
        view = self.env.ref("stock.stock_inventory_adjustment_name_form_view")
        return {
            "name": self.env._("Inventory Adjustment"),
            "type": "ir.actions.act_window",
            "views": [(view.id, "form")],
            "res_model": "stock.inventory.adjustment.name",
            "target": "new",
            "context": ctx,
        }
