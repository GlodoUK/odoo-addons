from odoo.tests import tagged

from .common import TestCpqCommon


@tagged("post_install", "-at_install")
class TestProductAttributeValueChar(TestCpqCommon):
    # _cpq_cast_custom_char

    def test_cpq_cast_custom_char_01(self):
        """Casting a valid string should return the stripped string."""
        self.assertEqual(
            self.prod_attrib_colour_custom._cpq_cast_custom_char("Hello"),
            "Hello",
        )

    def test_cpq_cast_custom_char_02(self):
        """Casting a string with whitespace should return the stripped string."""
        self.assertEqual(
            self.prod_attrib_colour_custom._cpq_cast_custom_char("  Hello  "),
            "Hello",
        )

    def test_cpq_cast_custom_char_03(self):
        """Casting an empty string should return an empty string."""
        self.assertEqual(
            self.prod_attrib_colour_custom._cpq_cast_custom_char(""),
            "",
        )

    def test_cpq_cast_custom_char_04(self):
        """Casting False should return an empty string."""
        self.assertEqual(
            self.prod_attrib_colour_custom._cpq_cast_custom_char(False),
            "",
        )

    # _cpq_sanitise_custom_char

    def test_cpq_sanitise_custom_char_01(self):
        """Sanitising a valid string should return the stripped string."""
        self.assertEqual(
            self.prod_attrib_colour_custom._cpq_sanitise_custom_char("Hello"),
            "Hello",
        )

    def test_cpq_sanitise_custom_char_02(self):
        """Sanitising a string with whitespace should strip it."""
        self.assertEqual(
            self.prod_attrib_colour_custom._cpq_sanitise_custom_char("  Hello  "),
            "Hello",
        )

    def test_cpq_sanitise_custom_char_03(self):
        """Sanitising an empty string should return an empty string."""
        self.assertEqual(
            self.prod_attrib_colour_custom._cpq_sanitise_custom_char(""),
            "",
        )

    def test_cpq_sanitise_custom_char_04(self):
        """Sanitising False should return an empty string."""
        self.assertEqual(
            self.prod_attrib_colour_custom._cpq_sanitise_custom_char(False),
            "",
        )

    # _cpq_validate_custom_char

    def test_cpq_validate_custom_char_01(self):
        """A non-empty string should pass validation."""
        self.assertTrue(
            self.prod_attrib_colour_custom._cpq_validate_custom_char("Hello"),
        )

    def test_cpq_validate_custom_char_02(self):
        """A whitespace-only string should fail validation."""
        self.assertFalse(
            self.prod_attrib_colour_custom._cpq_validate_custom_char("   "),
        )

    def test_cpq_validate_custom_char_03(self):
        """An empty string should fail validation."""
        self.assertFalse(
            self.prod_attrib_colour_custom._cpq_validate_custom_char(""),
        )

    def test_cpq_validate_custom_char_04(self):
        """A non-string value should fail validation."""
        self.assertFalse(
            self.prod_attrib_colour_custom._cpq_validate_custom_char(123),
        )

    def test_cpq_validate_custom_char_05(self):
        """None should fail validation."""
        self.assertFalse(
            self.prod_attrib_colour_custom._cpq_validate_custom_char(False),
        )


@tagged("post_install", "-at_install")
class TestProductAttributeValueFloat(TestCpqCommon):
    # _cpq_cast_custom_float

    def test_cpq_cast_custom_float_01(self):
        """Casting a numeric string should return the float."""
        self.assertEqual(
            self.prod_attrib_weight_custom._cpq_cast_custom_float("3.14"),
            3.14,
        )

    def test_cpq_cast_custom_float_02(self):
        """Casting a negative numeric string should return the float."""
        self.assertEqual(
            self.prod_attrib_weight_custom._cpq_cast_custom_float("-2.5"),
            -2.5,
        )

    def test_cpq_cast_custom_float_03(self):
        """Casting an integer string should return the float."""
        self.assertEqual(
            self.prod_attrib_weight_custom._cpq_cast_custom_float("42"),
            42.0,
        )

    def test_cpq_cast_custom_float_04(self):
        """Casting non-numeric input should raise ValueError."""
        with self.assertRaises(ValueError):
            self.prod_attrib_weight_custom._cpq_cast_custom_float("Not A Number")

    # _cpq_sanitise_custom_float

    def test_cpq_sanitise_custom_float_01(self):
        """Sanitising a numeric string should return the float."""
        self.assertEqual(
            self.prod_attrib_weight_custom._cpq_sanitise_custom_float("3.14"),
            3.14,
        )

    def test_cpq_sanitise_custom_float_02(self):
        """Sanitising a negative numeric string should return the float."""
        self.assertEqual(
            self.prod_attrib_weight_custom._cpq_sanitise_custom_float("-2.5"),
            -2.5,
        )

    def test_cpq_sanitise_custom_float_03(self):
        """Sanitising zero should return 0.0."""
        self.assertEqual(
            self.prod_attrib_weight_custom._cpq_sanitise_custom_float("0"),
            0.0,
        )

    def test_cpq_sanitise_custom_float_04(self):
        """Sanitising non-numeric input should raise ValueError."""
        with self.assertRaises(ValueError):
            self.prod_attrib_weight_custom._cpq_sanitise_custom_float("Not A Number")

    # _cpq_validate_custom_float

    def test_cpq_validate_custom_float_01(self):
        """A float string should pass validation."""
        self.assertTrue(
            self.prod_attrib_weight_custom._cpq_validate_custom_float("3.14"),
        )

    def test_cpq_validate_custom_float_02(self):
        """A negative float string should pass validation."""
        self.assertTrue(
            self.prod_attrib_weight_custom._cpq_validate_custom_float("-2.5"),
        )

    def test_cpq_validate_custom_float_03(self):
        """An integer string should pass validation as float."""
        self.assertTrue(
            self.prod_attrib_weight_custom._cpq_validate_custom_float("42"),
        )

    def test_cpq_validate_custom_float_04(self):
        """Non-numeric input should fail validation."""
        self.assertFalse(
            self.prod_attrib_weight_custom._cpq_validate_custom_float("Not A Number"),
        )

    def test_cpq_validate_custom_float_05(self):
        """False should fail validation."""
        self.assertFalse(
            self.prod_attrib_weight_custom._cpq_validate_custom_float(False),
        )

    def test_cpq_validate_custom_float_06(self):
        """Zero should pass validation."""
        self.assertTrue(
            self.prod_attrib_weight_custom._cpq_validate_custom_float("0"),
        )


@tagged("post_install", "-at_install")
class TestProductAttributeValueInteger(TestCpqCommon):
    # _cpq_cast_custom_integer

    def test_cpq_cast_custom_integer_01(self):
        """Casting a numeric string should return the integer."""
        self.assertEqual(
            self.prod_attrib_size_custom._cpq_cast_custom_integer("42"),
            42,
        )

    def test_cpq_cast_custom_integer_02(self):
        """Casting a negative numeric string should return the integer."""
        self.assertEqual(
            self.prod_attrib_size_custom._cpq_cast_custom_integer("-5"),
            -5,
        )

    def test_cpq_cast_custom_integer_03(self):
        """Casting zero should return 0."""
        self.assertEqual(
            self.prod_attrib_size_custom._cpq_cast_custom_integer("0"),
            0,
        )

    def test_cpq_cast_custom_integer_04(self):
        """Casting non-numeric input should raise ValueError."""
        with self.assertRaises(ValueError):
            self.prod_attrib_size_custom._cpq_cast_custom_integer("Not A Number")

    # _cpq_sanitise_custom_integer

    def test_cpq_sanitise_custom_integer_01(self):
        """Sanitising a numeric string should return the integer."""
        self.assertEqual(
            self.prod_attrib_size_custom._cpq_sanitise_custom_integer("42"),
            42,
        )

    def test_cpq_sanitise_custom_integer_02(self):
        """Sanitising a negative numeric string should return the integer."""
        self.assertEqual(
            self.prod_attrib_size_custom._cpq_sanitise_custom_integer("-5"),
            -5,
        )

    def test_cpq_sanitise_custom_integer_03(self):
        """Sanitising zero should return 0."""
        self.assertEqual(
            self.prod_attrib_size_custom._cpq_sanitise_custom_integer("0"),
            0,
        )

    def test_cpq_sanitise_custom_integer_04(self):
        """Sanitising non-numeric input should raise ValueError."""
        with self.assertRaises(ValueError):
            self.prod_attrib_size_custom._cpq_sanitise_custom_integer("Not A Number")

    # _cpq_validate_custom_integer

    def test_cpq_validate_custom_integer_01(self):
        """A numeric string should pass validation."""
        self.assertTrue(
            self.prod_attrib_size_custom._cpq_validate_custom_integer("42"),
        )

    def test_cpq_validate_custom_integer_02(self):
        """A negative numeric string should pass validation."""
        self.assertTrue(
            self.prod_attrib_size_custom._cpq_validate_custom_integer("-5"),
        )

    def test_cpq_validate_custom_integer_03(self):
        """Zero should pass validation."""
        self.assertTrue(
            self.prod_attrib_size_custom._cpq_validate_custom_integer("0"),
        )

    def test_cpq_validate_custom_integer_04(self):
        """Non-numeric input should fail validation."""
        self.assertFalse(
            self.prod_attrib_size_custom._cpq_validate_custom_integer("Not A Number"),
        )

    def test_cpq_validate_custom_integer_05(self):
        """False should fail validation."""
        self.assertFalse(
            self.prod_attrib_size_custom._cpq_validate_custom_integer(False),
        )

    def test_cpq_validate_custom_integer_06(self):
        """A float string should fail validation."""
        self.assertFalse(
            self.prod_attrib_size_custom._cpq_validate_custom_integer("3.9"),
        )
