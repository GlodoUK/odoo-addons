from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends(
        "order_line.force_invoiced_quantity",
        "order_line.price_total",
        "order_line.product_uom_qty",
    )
    def _compute_advance_payment(self):
        res = super()._compute_advance_payment()
        for order in self:
            invoiced_elsewhere = order.currency_id.round(
                sum(
                    line.price_total
                    / line.product_uom_qty
                    * line.force_invoiced_quantity
                    for line in order.order_line
                    if line.product_uom_qty and line.force_invoiced_quantity
                )
            )
            if not invoiced_elsewhere:
                continue
            order.amount_residual -= invoiced_elsewhere
            # As sale_advance_payment: a status only once there are advance
            # payments
            if order.payment_line_ids:
                order.advance_payment_status = (
                    "paid"
                    if order.currency_id.compare_amounts(order.amount_residual, 0) <= 0
                    else "partial"
                )
        return res
