from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _show_missing_delivery_wizard(self):
        self.ensure_one()
        return not self.order_line.filtered(lambda rec: rec.is_delivery)

    def action_check_delivery_confirm(self):
        for order in self:
            if order._show_missing_delivery_wizard():
                return {
                    "name": _("Missing Sale Shipping Charge"),
                    "view_mode": "form",
                    "res_model": "sale.order.missing.delivery",
                    "view_id": self.env.ref(
                        "sale_confirm_prompt_delivery.view_sale_order_missing_delivery_form"
                    ).id,
                    "type": "ir.actions.act_window",
                    "context": {"default_order_id": self.id},
                    "target": "new",
                }

        return self.action_confirm()
