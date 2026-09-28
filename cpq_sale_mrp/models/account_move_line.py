from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # fmt: off
    # ruff: noqa: E501, E741
    def _get_cogs_value(self):
        price_unit = super()._get_cogs_value()

        so_line = self.sale_line_ids and self.sale_line_ids[-1] or False
        if so_line and so_line.product_id.cpq_ok:
            # Use the CPQ dynamic BoM stored on the stock moves, which captures
            # the configuration-specific components generated at order time
            bom = (
                so_line.move_ids.filtered(lambda m: m.state != "cancel")
                .mapped("cpq_bom_id")
                .filtered(lambda b: b.type == "phantom")
                .with_context(skip_cpq_validate_ptav_ids=True)
            )
            if bom:
                is_line_reversing = self.move_id.move_type == "out_refund"
                account_moves = so_line.invoice_lines.move_id.filtered(lambda m: m.state == "posted" and bool(m.reversed_entry_id) == is_line_reversing)
                posted_invoice_lines = account_moves.line_ids.filtered(lambda l: l.display_type == "cogs" and l.product_id == self.product_id and l.balance > 0)
                qty_invoiced = sum([x.product_uom_id._compute_quantity(x.quantity, x.product_id.uom_id) for x in posted_invoice_lines])
                reversal_cogs = posted_invoice_lines.move_id.reversal_move_ids.line_ids.filtered(lambda l: l.display_type == "cogs" and l.product_id == self.product_id and l.balance > 0)
                qty_invoiced -= sum([line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id) for line in reversal_cogs])

                moves = so_line.move_ids
                average_price_unit = 0
                # Use the CPQ-aware explosion method to get configuration-specific component quantities
                for product, product_dict in bom._get_exploded_qty_dict(so_line.product_id).items():
                    factor = product_dict.get("qty")
                    prod_moves = moves.filtered(lambda m, product=product: m.product_id == product)
                    if not product.is_storable:
                        continue
                    product = product.with_company(self.company_id)
                    average_price_unit += factor * prod_moves._get_price_unit()
                price_unit = average_price_unit / bom.product_qty or price_unit
        return price_unit
    # fmt: on
