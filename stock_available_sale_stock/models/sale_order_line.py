from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    qty_immediately_usable_today = fields.Float(
        compute="_compute_availability_today",
        digits="Product Unit of Measure",
    )

    qty_potential_today = fields.Float(
        compute="_compute_availability_today",
        digits="Product Unit of Measure",
    )

    @api.depends("display_qty_widget", "product_id")
    def _compute_availability_today(self):
        self.qty_immediately_usable_today = 0.0
        self.qty_potential_today = 0.0

        todo = self.filtered(lambda o: o.display_qty_widget and o.product_id)

        for line in todo:
            product_id = line.product_id.with_context(
                location=line.order_id.warehouse_id.lot_stock_id.ids
            )

            line.qty_immediately_usable_today = product_id.immediately_usable_qty
            line.qty_potential_today = product_id.potential_qty
