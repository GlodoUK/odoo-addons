from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _compute_average_price(
        self, qty_invoiced, qty_to_invoice, stock_moves, is_returned=False
    ):
        self.ensure_one()
        if not self.cpq_ok:
            return super()._compute_average_price(
                qty_invoiced, qty_to_invoice, stock_moves, is_returned=is_returned
            )
        if stock_moves.product_id == self:
            return super()._compute_average_price(
                qty_invoiced, qty_to_invoice, stock_moves, is_returned=is_returned
            )
        bom = self.cpq_dynamic_bom_ids.filtered(lambda b: b.type == "phantom")
        if not bom:
            return super()._compute_average_price(
                qty_invoiced, qty_to_invoice, stock_moves, is_returned=is_returned
            )
        value = 0
        # XXX: If a product completely changes, then this will explode into a million
        # pieces, much like it does upstream in Odoo.
        components = bom.with_context(
            skip_cpq_validate_ptav_ids=True
        )._get_exploded_qty_dict(self)

        for component in components:
            line_qty = components[component]["qty"]
            moves = stock_moves.filtered(lambda m: m.product_id == component)  # noqa: B023
            value += line_qty * component._compute_average_price(
                qty_invoiced * line_qty,
                qty_to_invoice * line_qty,
                moves,
                is_returned=is_returned,
            )
        return value