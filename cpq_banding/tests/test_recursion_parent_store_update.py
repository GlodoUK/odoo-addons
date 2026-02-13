from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestCpqBandingCommon


@tagged("post_install", "-at_install")
class TestConstraints(TestCpqBandingCommon):
    def test_check_parent_id_01(self):
        """A banding cannot be its own parent."""
        with self.assertRaises(UserError):
            self.fabric.parent_id = self.fabric

    def test_check_parent_id_02(self):
        """A child cannot become the parent of its ancestor."""
        with self.assertRaises(UserError):
            self.cotton.parent_id = self.cotton_white

    def test_check_parent_id_03(self):
        """A grandchild cannot become the parent of the root."""
        with self.assertRaises(UserError):
            self.fabric.parent_id = self.cotton_white
