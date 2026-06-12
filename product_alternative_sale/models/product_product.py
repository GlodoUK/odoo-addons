from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_alternatives_preview(self, limit=None, sale_ok=True):
        """
        Display data for the order-line popover: the first ``limit``
        sellable alternatives plus a count of how many more there are.
        """
        self.ensure_one()
        if limit is None:
            limit = 5
        alternatives = self._get_alternative_products()
        if sale_ok:
            alternatives = alternatives.filtered("sale_ok")
        preview = alternatives[:limit]
        return {
            "alternatives": [
                {"id": product.id, "display_name": product.display_name}
                for product in preview
            ],
            "remaining": len(alternatives) - len(preview),
        }
