from odoo import models


class ProductTemplateMetaLine(models.Model):
    _inherit = "product.template.meta.line"

    def _get_sale_order_line_vals(self, line):
        self.ensure_one()

        product_id = self._get_child_product_variant(
            line=line,
        )

        sale_order_line = line.new(
            {
                "meta_tmpl_line_id": self.id,
                "order_id": line.order_id.id,
                "sequence": line.sequence,
                "product_id": product_id.id,
                "meta_parent_line_id": line.id,
                "company_id": line.order_id.company_id.id,
            }
        )
        sale_order_line.product_id_change()
        sale_order_line.product_uom_qty = self.quantity * line.product_uom_qty
        sale_order_line.product_uom_change()
        sale_order_line._onchange_discount()
        vals = sale_order_line._convert_to_write(sale_order_line._cache)
        vals.update({"price_unit": 0.0})
        return vals
