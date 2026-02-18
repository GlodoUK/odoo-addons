from odoo.tests import tagged

from .common import TestCpqBandingCommon


@tagged("post_install", "-at_install")
class TestCpqBanding(TestCpqBandingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_is_leaf_01(self):
        """Root"""
        self.assertFalse(
            self.fabric.is_leaf,
        )

    def test_is_leaf_02(self):
        """Children"""
        self.assertFalse(
            self.cotton.is_leaf,
        )

        self.assertFalse(
            self.leather.is_leaf,
        )

    def test_is_leaf_03(self):
        """Grandchildren"""
        self.assertTrue(
            self.cotton_white.is_leaf,
        )

        self.assertTrue(
            self.leather_tan.is_leaf,
        )

    def test_children_count_01(self):
        """Root should count all descendants."""
        self.assertEqual(
            self.fabric.child_count,
            4,
        )

    def test_children_count_02(self):
        """Child should count its descendants."""
        self.assertEqual(
            self.cotton.child_count,
            1,
        )

    def test_children_count_03(self):
        """Grandchild should have no descendants."""
        self.assertEqual(
            self.cotton_white.child_count,
            0,
        )
