from odoo import models
from odoo.fields import Domain


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_product_catalog_domain(self):
        """Restrict the catalog to a set of variants when opened from the
        alternatives popover (context key set by
        ``sale.order.line.action_view_alternatives_catalog``)."""
        domain = super()._get_product_catalog_domain()
        variant_ids = self.env.context.get("product_alternative_sale_ids")
        if variant_ids:
            domain &= Domain("id", "in", variant_ids)
        return domain
