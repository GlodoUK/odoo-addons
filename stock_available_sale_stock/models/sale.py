from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    qty_immediately_usable_today = fields.Float(
        compute="_compute_availability_today", digits="Product Unit of Measure"
    )
    qty_potential_today = fields.Float(
        compute="_compute_availability_today", digits="Product Unit of Measure"
    )

    @api.depends(
        "product_id",
        "display_qty_widget",
    )
    def _compute_availability_today(self):
        for record in self:
            if not record.product_id or not record.display_qty_widget:
                record.qty_immediately_usable_today = False
                record.qty_potential_today = False
                continue

            product_id = record.product_id.with_context(
                location=record.order_id.warehouse_id.lot_stock_id.ids
            )

            record.qty_immediately_usable_today = product_id.immediately_usable_qty
            record.qty_potential_today = product_id.potential_qty
