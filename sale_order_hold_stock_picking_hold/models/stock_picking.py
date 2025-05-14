from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_unhold(self, **kwargs):
        if any(self.mapped("group_id.sale_id.hold")):
            msg = _("The parent sales order is still on hold.")
            raise UserError(msg)

        return super().action_unhold(**kwargs)
