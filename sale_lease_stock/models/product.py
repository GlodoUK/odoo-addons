from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    lease_ok = fields.Boolean(
        string="Can be Leased",
        help="Allow leasing of this product.",
        index=True,
        copy=True,
    )
    lease_pricing_ids = fields.One2many(
        "sale_lease_stock.pricing",
        "product_template_id",
        string="Lease Pricings",
        auto_join=True,
        copy=True,
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_lease_price_rules(self, **kwargs):
        self.ensure_one()

        if not self.lease_ok:
            return self.env["sale_lease_stock.pricing"]

        pricelist = kwargs.get("pricelist", self.env["product.pricelist"])

        # Alternatively we can use the following domain.
        # This filter works better for smaller lists.
        # [
        #     '&',
        #     '&',
        #     ('product_template_id', '=', product_template_id),
        #     '|',
        #     ('product_variant_ids', '=', False),
        #     ('product_variant_ids.id', '=', product_id),
        #     '|',
        #     ('pricelist_id', '=', False),
        #     ('pricelist_id', '=', parent.pricelist_id)
        # ]

        available_pricings = self.sudo().lease_pricing_ids.filtered(
            lambda p: p.pricelist_id == pricelist
        )
        if not available_pricings:
            # If no pricing is defined for given pricelist:
            # fallback on generic pricings
            available_pricings = self.lease_pricing_ids.filtered(
                lambda p: not p.pricelist_id
            )

        return available_pricings.filtered(lambda r: r.applies_to(self))
