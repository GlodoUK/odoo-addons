from odoo import models

from odoo.addons.base_search_rank.fields import SearchRank


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "base_search_rank.mixin"]

    # display_name decomposed into its stored constituents: it is non-stored
    # and context/language-dependent, so it cannot anchor a stored document
    search_rank = SearchRank(
        sources=(
            "=default_code",
            "product_tmpl_id.name",
            "product_template_attribute_value_ids.name",
            "barcode",
        ),
    )
