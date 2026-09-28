from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    alternative_rule_ids = fields.One2many(
        "product.alternative",
        "product_tmpl_id",
        string="Alternatives",
        help="Products proposed as alternatives to this one.",
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_alternative_products(self):
        """Return the resolved ``product.product`` alternatives for this
        variant: the template's alternative definitions whose source-side scope
        matches this variant, resolved to their target variants."""
        self.ensure_one()
        applicable = self.product_tmpl_id.alternative_rule_ids.filtered(
            lambda alt: alt._matches_source_variant(self)
        )
        return applicable._get_alternative_variants()
