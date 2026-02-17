from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_total_routes(self):
        routes = super().get_total_routes()
        if not routes.filtered(
            lambda r: any(rule.action == "manufacture" for rule in r.rule_ids)
        ):
            has_dynamic_bom = self.product_tmpl_id.cpq_dynamic_bom_ids.filtered(
                lambda b: b.type == "normal"
            )
            if has_dynamic_bom:
                manufacture_routes = (
                    self.env["stock.rule"]
                    .search([("action", "=", "manufacture")])
                    .route_id
                )
                routes |= manufacture_routes
        return routes
