from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _compute_tax_id(self):
        has_variant_supplier_taxes_id = self.filtered(
            lambda line: line.variant_supplier_taxes_id
        )

        for line in has_variant_supplier_taxes_id:
            line = line.with_company(line.company_id)
            fpos = (
                line.order_id.fiscal_position_id
                or line.order_id.fiscal_position_id._get_fiscal_position(
                    line.order_id.partner_id
                )
            )
            taxes = line.product_id.variant_supplier_taxes_id._filter_taxes_by_company(
                line.company_id
            )
            line.taxes_id = fpos.map_tax(taxes)

        return super(
            PurchaseOrderLine, self - has_variant_supplier_taxes_id
        )._compute_purchase_price()
