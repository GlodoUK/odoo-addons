from odoo import models


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    def init(self):
        res = super().init()
        indexes_to_remove = [
            "DROP INDEX IF EXISTS test_product_supplerinfo_product_id",
        ]
        for index in indexes_to_remove:
            self.env.cr.execute(index)

        indexes = [
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_supplerinfo_product_id ON product_supplierinfo USING btree (product_id)",  # noqa: E501
        ]
        for index in indexes:
            self.env.cr.execute(index)
        return res
