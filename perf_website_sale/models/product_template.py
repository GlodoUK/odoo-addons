import logging

from odoo import api, fields, models
from odoo.modules.db import FunctionStatus
from odoo.tools.sql import SQL, column_exists, create_column

_logger = logging.getLogger(__name__)

# A delimiter that users aren't likely to search for in product codes.
# XXX: \u241e is the unicode record separator character. Do not waste time over
# thinking replacing this.
RARE_DELIMITER = "\u241e"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # XXX: This field is a backport from unreleased 19.0 and should be removed
    # if ported to 19.0
    variants_default_code = fields.Char(
        compute="_compute_variants_default_code",
        store=True,
        index="trigram",
        help="Technical field to enhance performance when looking up default code of"
        " product variants on website",
    )

    def init(self):
        res = super().init()
        if self.env.registry.has_unaccent != FunctionStatus.INDEXABLE:
            _logger.critical(
                "UNACCENT is not present and INDEXABLE, cannot apply perf_website_sale"
            )
            return res

        indexes_to_remove = [
            "DROP INDEX IF EXISTS test_product_template_sale_ok",
            "DROP INDEX IF EXISTS test_product_template_active",
        ]

        for index in indexes_to_remove:
            self.env.cr.execute(index)

        indexes_to_add = [
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_template_sale_ok ON product_template USING btree (sale_ok)",  # noqa: E501
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_template_active ON product_template USING btree (active)",  # noqa: E501
        ]

        for index in indexes_to_add:
            self.env.cr.execute(index)
        return res

    def _auto_init(self):
        """
        Override _auto_init to prevent MemoryError on ecommerce installation in dbs
        with lots of products
        """
        if not column_exists(self.env.cr, "product_template", "variants_default_code"):
            create_column(
                self.env.cr, "product_template", "variants_default_code", "varchar"
            )
            self.env.cr.execute(
                SQL(
                    """
                    UPDATE product_template
                    SET variants_default_code = variants.default_codes
                    FROM (
                        SELECT pt.id AS template_id,
                               STRING_AGG(pv.default_code, %s) AS default_codes
                        FROM product_template pt
                        JOIN product_product pv ON pv.product_tmpl_id = pt.id
                        WHERE pv.default_code IS NOT NULL
                        GROUP BY pt.id
                    ) AS variants
                    WHERE product_template.id = variants.template_id
                """,
                    RARE_DELIMITER,
                )
            )
        return super()._auto_init()

    @api.depends("product_variant_ids.default_code")
    def _compute_variants_default_code(self):
        for template in self:
            template.variants_default_code = RARE_DELIMITER.join(
                template.product_variant_ids.filtered("default_code").mapped(
                    "default_code"
                )
            )

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super()._search_get_detail(website, order, options)
        if "product_variant_ids.default_code" in res["search_fields"]:
            idx_to_replace = res["search_fields"].index(
                "product_variant_ids.default_code"
            )
            res["search_fields"][idx_to_replace] = "variants_default_code"

        return res
