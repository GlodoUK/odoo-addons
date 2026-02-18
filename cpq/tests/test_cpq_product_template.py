from odoo.tests import tagged

from .common import TestCpqCommon


@tagged("post_install", "-at_install")
class TestCpqProductTemplate(TestCpqCommon):
    def test_cpq_product_variant_count_cpq(self):
        """A CPQ product with no variants should report count of one."""
        self.assertFalse(
            self.product_tmpl.product_variant_ids,
        )

        self.assertEqual(
            self.product_tmpl.product_variant_count,
            1,
        )
