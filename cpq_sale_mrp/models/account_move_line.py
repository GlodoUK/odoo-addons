from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _stock_account_get_anglo_saxon_price_unit(self):
        price_unit = super()._stock_account_get_anglo_saxon_price_unit()

        sale_line_id = fields.first(self.sale_line_ids).with_context(active_test=False)
        bom = self.env["cpq.dynamic.bom"]
        if sale_line_id.product_id.cpq_ok:
            # Find the relevant dynamic phantom BoM
            bom = (
                sale_line_id.move_ids.mapped("cpq_bom_id")
                .filtered(lambda b: b.type == "phantom")
                .with_context(skip_cpq_validate_ptav_ids=True)
            )

        if not bom:
            return price_unit

        if len(bom) > 1:
            raise ValidationError(
                _("Found more than one CPQ Dynamic BoM. This should not have happened.")
            )

        is_line_reversing = self.move_id.move_type == "out_refund"
        qty_to_invoice = self.product_uom_id._compute_quantity(
            self.quantity, self.product_id.uom_id
        )
        account_moves = sale_line_id.invoice_lines.move_id.filtered(
            lambda m: m.state == "posted"
            and bool(m.reversed_entry_id) == is_line_reversing
        )
        posted_invoice_lines = account_moves.line_ids.filtered(
            lambda i: i.is_anglo_saxon_line
            and i.product_id == self.product_id
            and i.balance > 0
        )
        qty_invoiced = sum(
            x.product_uom_id._compute_quantity(x.quantity, x.product_id.uom_id)
            for x in posted_invoice_lines
        )
        reversal_cogs = posted_invoice_lines.move_id.reversal_move_id.line_ids.filtered(
            lambda i: i.is_anglo_saxon_line
            and i.product_id == self.product_id
            and i.balance > 0
        )
        qty_invoiced -= sum(
            line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
            for line in reversal_cogs
        )

        moves = sale_line_id.move_ids
        average_price_unit = 0
        for product, product_dict in bom._get_exploded_qty_dict(
            sale_line_id.product_id
        ).items():
            factor = product_dict.get("qty")
            prod_moves = moves.filtered(
                lambda m, product=product: m.product_id == product
            )
            prod_qty_invoiced = factor * qty_invoiced
            prod_qty_to_invoice = factor * qty_to_invoice
            product = product.with_company(self.company_id).with_context(
                is_returned=is_line_reversing
            )
            average_price_unit += factor * product._compute_average_price(
                prod_qty_invoiced, prod_qty_to_invoice, prod_moves
            )
        price_unit = average_price_unit / bom.product_qty or price_unit
        price_unit = self.product_id.uom_id._compute_price(
            price_unit, self.product_uom_id
        )

        return price_unit
