from odoo.tests import tagged

from .common import TestCpqBandingCommon


@tagged("post_install", "-at_install")
class TestCombinationInfo(TestCpqBandingCommon):
    # ruff: noqa: E501
    def _get_banding_ptav(self):
        return self.product_tmpl.valid_product_template_attribute_line_ids.product_template_value_ids.filtered(
            lambda v: v.cpq_custom_type == "banding"
        )

    def test_combination_info(self):
        """Selection values should only contain leaf bandings"""
        ptav = self._get_banding_ptav()
        info = ptav._cpq_get_combination_info()

        selection_ids = {v[0] for v in info["cpq_selection_values"]}

        self.assertIn(
            self.cotton_white.id,
            selection_ids,
        )

        self.assertIn(
            self.leather_tan.id,
            selection_ids,
        )

        self.assertNotIn(
            self.fabric.id,
            selection_ids,
        )

        self.assertNotIn(
            self.cotton.id,
            selection_ids,
        )

        self.assertNotIn(
            self.leather.id,
            selection_ids,
        )
