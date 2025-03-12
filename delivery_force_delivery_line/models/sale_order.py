from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import config


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        check_missing_delivery_line = (
            config["test_enable"] 
            and self.env.context.get("test_delivery_force_delivery_line")
        ) or not config["test_enable"]
        if check_missing_delivery_line:
            for order in self:
                if not order.order_line.filtered(lambda o: o.is_delivery):
                    raise UserError(
                        _(
                            "All orders must contain a delivery line!\n\n"
                            "Please use the 'Add Shipping' button to add a delivery line."
                        )
                    )
        return super().action_confirm()
