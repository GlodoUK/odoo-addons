from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    force_delivered_quantity = fields.Float(
        digits="Product Unit",
        copy=False,
        help="Counted as delivered, and as already procured, on top of what the"
        " line's moves deliver: goods that went out some other way - before"
        " go-live, say - and must neither be delivered again nor picked.",
    )

    @api.depends("force_delivered_quantity")
    def _compute_qty_delivered(self):
        return super()._compute_qty_delivered()

    def _prepare_qty_delivered(self):
        """Add the forced quantity to what the line's moves delivered.

        Additive, and only for a line whose delivered quantity is computed: a
        'manual' line's qty_delivered is what someone typed, and core only
        overwrites it for lines this mapping carries.
        """
        delivered_qties = super()._prepare_qty_delivered()
        for line in self:
            if line.force_delivered_quantity and line.qty_delivered_method != "manual":
                delivered_qties[line] = (
                    delivered_qties.get(line, 0.0) + line.force_delivered_quantity
                )
        return delivered_qties

    def _get_qty_procurement(self, previous_product_uom_qty=False):
        """Count the forced quantity as procured already.

        What stops confirming - or any later procurement run, after a quantity
        change say - ordering goods that were delivered without a move.
        """
        qty = super()._get_qty_procurement(
            previous_product_uom_qty=previous_product_uom_qty
        )
        return qty + self.force_delivered_quantity
