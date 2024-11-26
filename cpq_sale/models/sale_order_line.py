from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_template_id_cpq_ok = fields.Boolean(related="product_template_id.cpq_ok")

    @api.onchange("product_id")
    def product_id_change(self):
        res = super().product_id_change()
        if self.product_id.cpq_ok and self.product_id.cpq_description_sale_tmpl:
            product = self.product_id.with_context(lang=self.order_id.partner_id.lang)

            name = product.product_tmpl_id._cpq_render_inline_template(
                product.cpq_description_sale_tmpl,
                extras={
                    "record": product,
                    "tmpl": self,
                },
            )

            if name:
                self.name = name
        return res
