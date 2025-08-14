import logging

from odoo import models
from odoo.modules.db import FunctionStatus

_logger = logging.getLogger(__name__)


class ProductTag(models.Model):
    _inherit = "product.tag"

    def init(self):
        res = super().init()
        if self.env.registry.has_unaccent != FunctionStatus.INDEXABLE:
            _logger.critical(
                "UNACCENT is not present and INDEXABLE, cannot apply perf_website_sale"
            )
            return res

        indexes_to_remove = [
            "DROP INDEX IF EXISTS test_product_tag_visible_on_ecommerce",
            "DROP INDEX IF EXISTS test_product_tag_sequence",
        ]
        for index in indexes_to_remove:
            self.env.cr.execute(index)

        indexes = [
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_tag_visible_on_ecommerce ON product_tag USING btree (visible_on_ecommerce)",  # noqa: E501
            "CREATE INDEX IF NOT EXISTS perf_website_sale_product_tag_sequence ON product_tag USING btree (sequence)",  # noqa: E501
        ]
        for index in indexes:
            self.env.cr.execute(index)
        return res
