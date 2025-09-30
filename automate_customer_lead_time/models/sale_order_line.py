from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("product_id", "product_uom_qty")
    def _compute_customer_lead(self):
        res = super()._compute_customer_lead()
        # Adjust lead time to account for vendor time
        for line in self:
            product = line.product_id
            vendor_lead_time = line._get_vendor_lead_time()
            if product.sale_delay_method == "add":
                line.customer_lead += vendor_lead_time
            elif product.sale_delay_method == "replace":
                line.customer_lead = vendor_lead_time
            elif product.sale_delay_method == "max":
                line.customer_lead = max(line.customer_lead, vendor_lead_time)
            elif product.sale_delay_method == "min":
                line.customer_lead = min(line.customer_lead, vendor_lead_time)
        return res

    def _get_vendor_lead_time(self):
        self.ensure_one()
        product = self.product_id
        if not product:
            return 0.0
        seller = product._select_seller(
            quantity=self.product_uom_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
        )
        return seller and seller.delay or 0.0
