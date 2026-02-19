from odoo.tests import tagged

from .common import TestCpqBandingCommon


@tagged("post_install", "-at_install")
class TestProductAttributeValue(TestCpqBandingCommon):
    # _cpq_cast_custom_banding

    def test_cpq_cast_custom_banding_01(self):
        """Casting the root banding id should return an empty recordset."""
        self.assertFalse(
            self.attr_value_banding._cpq_cast_custom_banding(
                str(self.fabric.id),
            ),
        )

    def test_cpq_cast_custom_banding_02(self):
        """Casting the child banding id should return an empty recordset."""
        self.assertFalse(
            self.attr_value_banding._cpq_cast_custom_banding(
                str(self.cotton.id),
            ),
        )

    def test_cpq_cast_custom_banding_03(self):
        """Casting the grandchild banding id should return the banding record."""
        self.assertEqual(
            self.attr_value_banding._cpq_cast_custom_banding(
                str(self.cotton_white.id),
            ),
            self.cotton_white,
        )

    def test_cpq_cast_custom_banding_04(self):
        """Casting non-numeric input should return an empty recordset."""
        self.assertFalse(
            self.attr_value_banding._cpq_cast_custom_banding("Not A Number"),
        )

    # _cpq_sanitise_custom_banding

    def test_cpq_sanitise_custom_banding_01(self):
        """Sanitising the root banding id should return False."""
        self.assertFalse(
            self.attr_value_banding._cpq_sanitise_custom_banding(
                str(self.fabric.id),
            ),
        )

    def test_cpq_sanitise_custom_banding_02(self):
        """Sanitising the child banding id should return False."""
        self.assertFalse(
            self.attr_value_banding._cpq_sanitise_custom_banding(
                str(self.cotton.id),
            ),
        )

    def test_cpq_sanitise_custom_banding_03(self):
        """Sanitising a valid leaf id should return the integer id."""
        self.assertEqual(
            self.attr_value_banding._cpq_sanitise_custom_banding(
                str(self.cotton_white.id),
            ),
            self.cotton_white.id,
        )

    def test_cpq_sanitise_custom_banding_04(self):
        """Sanitising non-numeric input should return False."""
        self.assertFalse(
            self.attr_value_banding._cpq_sanitise_custom_banding("Not A Number"),
        )

    # _cpq_validate_custom_banding

    def test_cpq_validate_custom_banding_01(self):
        """The root banding id should fail validation."""
        self.assertFalse(
            self.attr_value_banding._cpq_validate_custom_banding(
                str(self.fabric.id),
            ),
        )

    def test_cpq_validate_custom_banding_02(self):
        """The child banding id should fail validation."""
        self.assertFalse(
            self.attr_value_banding._cpq_validate_custom_banding(
                str(self.cotton.id),
            ),
        )

    def test_cpq_validate_custom_banding_03(self):
        """The grandchild banding id should pass validation."""
        self.assertTrue(
            self.attr_value_banding._cpq_validate_custom_banding(
                str(self.cotton_white.id),
            ),
        )

    def test_cpq_validate_custom_banding_04(self):
        """Non-numeric input should fail validation."""
        self.assertFalse(
            self.attr_value_banding._cpq_validate_custom_banding("Not A Number"),
        )
