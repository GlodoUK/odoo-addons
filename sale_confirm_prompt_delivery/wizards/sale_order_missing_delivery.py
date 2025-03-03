from odoo import fields, models


class SaleOrderMissingDelivery(models.TransientModel):
    _name = "sale.order.missing.delivery"
    _description = "Sales Order Missing Delivery"

    order_id = fields.Many2one(
        "sale.order", string="Sale Order", required=True, ondelete="cascade"
    )

    def action_confirm(self):
        return self.order_id.action_confirm()

    def action_add_shipping(self):
        return self.order_id.action_open_delivery_wizard()
