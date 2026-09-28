from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    display_alternatives_widget = fields.Boolean(
        compute="_compute_display_alternatives_widget",
    )

    @api.depends("product_id")
    def _compute_display_alternatives_widget(self):
        # Materialised variants only: _get_alternative_products() never creates
        # variants. Alternatives on a dynamic template with no materialised
        # variants therefore won't appear here or in the catalog -- ordering a
        # new dynamic configuration would need the configurator (out of scope).
        for line in self:
            matched = False
            if not line.product_id:
                line.display_alternatives_widget = False
                continue

            for alternative in line.product_id.product_tmpl_id.alternative_rule_ids:
                if not alternative._matches_source_variant(self):
                    continue
                if alternative._get_alternative_variants().filtered("sale_ok"):
                    matched = True
                    break

            line.display_alternatives_widget = matched

    def action_view_alternatives_catalog(self):
        """Open the product catalog for this line's order, restricted to this
        line's alternative variants."""
        self.ensure_one()
        return self.with_context(
            order_id=self.order_id.id,
            product_alternative_sale_ids=self.product_id._get_alternative_products()
            .filtered("sale_ok")
            .ids,
        ).action_add_from_catalog()
