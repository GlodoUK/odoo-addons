from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        for order in self:
            if not order.order_line.filtered(lambda o: o.is_delivery):
                raise UserError(
                    _(
                        "All orders must contain a delivery line!\n\n"
                        "Please use the 'Add Shipping' button to add a delivery line."
                    )
                )
        return super().action_confirm()
