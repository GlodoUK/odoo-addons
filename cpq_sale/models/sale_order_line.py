from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_template_id_cpq_ok = fields.Boolean(
        related="product_template_id.cpq_ok",
    )

    def _compute_name(self):
        res = super()._compute_name()

        for line in self:
            if (
                not line.product_id.cpq_ok
                or not line.product_id.cpq_description_sale_tmpl
            ):
                continue

            lang = line.order_id._get_lang()
            if lang != self.env.lang:
                line = line.with_context(lang=lang)

            render_values = {
                "record": line.product_id,
                "tmpl": line.product_id.product_tmpl_id,
            }
            cpq_name = line.product_id.product_tmpl_id._cpq_render_inline_template(
                line.product_id.cpq_description_sale_tmpl,
                extras=render_values,
            )

            if cpq_name:
                line.name = cpq_name

        return res
