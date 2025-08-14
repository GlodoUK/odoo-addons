from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def init(self):
        res = super().init()
        indexes_to_remove = [
            "DROP INDEX IF EXISTS test_product_product_default_code_unaccent",
            "DROP INDEX IF EXISTS test_product_product_barcode_unaccent",
            "DROP INDEX IF EXISTS test_product_product_active",
        ]
        for index in indexes_to_remove:
            self.env.cr.execute(index)

        indexes_to_add = [
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_product_active ON product_product USING btree (active)",  # noqa: E501
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_product_default_code_unaccent ON product_product USING gin (unaccent((default_code)::text) gin_trgm_ops)",  # noqa: E501
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_product_barcode_unaccent ON product_product USING gin (unaccent((barcode)::text) gin_trgm_ops)",  # noqa: E501
        ]

        for index in indexes_to_add:
            self.env.cr.execute(index)
        return res
