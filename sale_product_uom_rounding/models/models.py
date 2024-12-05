from odoo import models, api
from odoo.tools import float_round


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        uom = self.product_uom
        qty = self.product_uom_qty

        if uom and qty:
            qty = float_round(
                qty, precision_rounding=uom.rounding, rounding_method='UP'
            )
            self.product_uom_qty = qty

        return super(SaleOrderLine, self).product_uom_change()
