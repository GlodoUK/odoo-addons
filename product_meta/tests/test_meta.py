from odoo.exceptions import ValidationError

from .common import TestMetaCommon


class TestMeta(TestMetaCommon):
    def test_unrelated(self):
        with self.assertRaises(ValidationError):
            self.product_meta_1.write(
                {
                    "meta_product_tmpl_line_ids": [
                        (
                            0,
                            0,
                            {
                                "child_tmpl_id": self.product_b.product_tmpl_id.id,
                                "child_variant_id": self.product_a.id,
                                "quantity": 1.0,
                            },
                        )
                    ]
                }
            )

    def test_recursion(self):
        with self.assertRaises(ValidationError):
            self.product_meta_1.write(
                {
                    "meta_product_tmpl_line_ids": [
                        (
                            0,
                            0,
                            {
                                "child_tmpl_id": self.product_meta_2.id,
                                "child_variant_id": self.product_meta_2.product_variant_ids.id,
                                "quantity": 1.0,
                            },
                        )
                    ]
                }
            )

    def test_get_child_product_variant(self):
        meta_line_ids = self.product_meta_1.meta_product_tmpl_line_ids

        for meta_line_id in meta_line_ids:
            self.assertEqual(
                meta_line_id.child_variant_id,
                meta_line_id._get_child_product_variant(),
            )
