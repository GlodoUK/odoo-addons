from odoo import api, models


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
        )._compute_tax_id()

    @api.model
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier, po):
        res = super()._prepare_purchase_order_line(product_id, product_qty, product_uom, company_id, supplier, po)

        if product_id.variant_supplier_taxes_id:
            product_taxes = product_id.variant_supplier_taxes_id.filtered(lambda x: x.company_id in company_id.parent_ids)
            taxes = po.fiscal_position_id.map_tax(product_taxes)
            res["taxes_id"] = taxes

        return res

