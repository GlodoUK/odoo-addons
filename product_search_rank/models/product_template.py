from odoo import models

from odoo.addons.base_search_rank.fields import SearchRank


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "base_search_rank.mixin"]

    # the template's own default_code/barcode are non-stored computes over
    # the variants, so the document (and the exact boost, via a one2many
    # hop) reads the variant columns directly
    search_rank = SearchRank(
        sources=(
            "=product_variant_ids.default_code",
            "name",
            "product_variant_ids.barcode",
        ),
    )
