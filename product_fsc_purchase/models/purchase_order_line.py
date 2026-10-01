from odoo import models


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "product_fsc.line.mixin"]

    def _prepare_account_move_line(self, move=False):
        # Carry the order's frozen claim onto the vendor bill.
        values = super()._prepare_account_move_line(move=move)
        values["fsc_label"] = self.fsc_label
        return values
