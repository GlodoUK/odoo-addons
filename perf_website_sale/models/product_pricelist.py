from odoo import models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def init(self):
        res = super().init()
        indexes_to_remove = [
            "DROP INDEX IF EXISTS test_product_pricelist_item_product_id",
            "DROP INDEX IF EXISTS test_product_pricelist_item_product_tmpl_id",
            "DROP INDEX IF EXISTS test_product_pricelist_item_applied_on",
            "DROP INDEX IF EXISTS test_product_pricelist_item_min_quantity",
            "DROP INDEX IF EXISTS test_product_pricelist_item_categ_id",
            "DROP INDEX IF EXISTS test_product_pricelist_item_company_id",
        ]
        for index in indexes_to_remove:
            self.env.cr.execute(index)

        indexes_to_add = [
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_pricelist_item_product_id ON product_pricelist_item USING btree (product_id)",  # noqa: E501
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_pricelist_item_product_tmpl_id ON product_pricelist_item USING btree (product_tmpl_id)",  # noqa: E501
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_pricelist_item_applied_on ON product_pricelist_item USING btree (applied_on)",  # noqa: E501
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_pricelist_item_min_quantity ON product_pricelist_item USING btree (min_quantity)",  # noqa: E501
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_pricelist_item_categ_id ON product_pricelist_item USING btree (categ_id)",  # noqa: E501
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_pricelist_item_company_id ON product_pricelist_item USING btree (company_id)",  # noqa: E501
        ]

        for index in indexes_to_add:
            self.env.cr.execute(index)
        return res
