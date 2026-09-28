from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _pricelist_check_sale_behaviour(self):
        # Delivery cost lines carry the carrier's delivery product, which is
        # not expected to be priced on the customer's pricelist.
        self.ensure_one()
        if self.is_delivery:
            return True
        return super()._pricelist_check_sale_behaviour()
