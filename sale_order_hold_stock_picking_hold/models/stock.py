from odoo import _, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        res.update({"hold": self.sale_line_id.order_id.hold})
        return res


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_unhold(self, **kwargs):
        if True in self.mapped("group_id.sale_id.hold"):
            raise UserError(
                _("Cannot release from hold when the parent Sale Order is still held.")
            )

        return super().action_unhold(**kwargs)
