from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestStockLocationFreeze(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

        cls.stock_location.frozen = False

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )

        # Create sub-locations for testing
        cls.sublocation_a = cls.env["stock.location"].create(
            {
                "name": "Test Sublocation A",
                "location_id": cls.stock_location.id,
                "usage": "internal",
            }
        )
        cls.sublocation_b = cls.env["stock.location"].create(
            {
                "name": "Test Sublocation B",
                "location_id": cls.stock_location.id,
                "usage": "internal",
            }
        )
        # Create a nested sub-location under sublocation_a
        cls.nested_sublocation = cls.env["stock.location"].create(
            {
                "name": "Nested Sublocation",
                "location_id": cls.sublocation_a.id,
                "usage": "internal",
            }
        )

    def _create_quant(self, product, location, qty):
        """Helper to create a quant with stock in a location."""
        self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "location_id": location.id,
                "quantity": qty,
            }
        )

    def test_freeze_parent_blocks_reservations_and_movements(self):
        """
        Test that freezing WH/Stock prevents reservations and movements
        in WH/Stock and all sub-locations.
        """
        # Add stock to various locations before freezing
        self._create_quant(self.product, self.stock_location, 10.0)
        self._create_quant(self.product, self.sublocation_a, 10.0)
        self._create_quant(self.product, self.sublocation_b, 10.0)
        self._create_quant(self.product, self.nested_sublocation, 10.0)

        # Freeze WH/Stock
        self.stock_location.frozen = True

        # Verify frozen_parent_path is computed correctly
        self.assertTrue(self.stock_location.frozen_parent_path)
        self.assertTrue(self.sublocation_a.frozen_parent_path)
        self.assertTrue(self.sublocation_b.frozen_parent_path)
        self.assertTrue(self.nested_sublocation.frozen_parent_path)

        # Test: Cannot update available quantity in WH/Stock (move stock in)
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_available_quantity(
                self.product, self.stock_location, 5.0
            )

        # Test: Cannot update available quantity in sublocation_a
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_available_quantity(
                self.product, self.sublocation_a, 5.0
            )

        # Test: Cannot update available quantity in nested_sublocation
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_available_quantity(
                self.product, self.nested_sublocation, 5.0
            )

        # Test: Cannot reserve stock in WH/Stock
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_reserved_quantity(
                self.product, self.stock_location, 5.0
            )

        # Test: Cannot reserve stock in sublocation_a
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_reserved_quantity(
                self.product, self.sublocation_a, 5.0
            )

        # Test: Cannot reserve stock in sublocation_b
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_reserved_quantity(
                self.product, self.sublocation_b, 5.0
            )

        # Test: Cannot reserve stock in nested_sublocation
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_reserved_quantity(
                self.product, self.nested_sublocation, 5.0
            )

        # Unfreeze WH/Stock and verify operations are now allowed
        self.stock_location.frozen = False

        self.assertFalse(self.stock_location.frozen_parent_path)
        self.assertFalse(self.sublocation_a.frozen_parent_path)

        # Should now be able to update quantities
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 5.0
        )
        self.env["stock.quant"]._update_reserved_quantity(
            self.product, self.sublocation_a, 5.0
        )

    def test_freeze_sublocation_allows_parent_operations(self):
        """
        Test that freezing only a sub-location allows reservations and movements
        against the parent location, but blocks them for the frozen sub-location.
        """
        # Add stock to various locations before freezing
        self._create_quant(self.product, self.stock_location, 10.0)
        self._create_quant(self.product, self.sublocation_a, 10.0)
        self._create_quant(self.product, self.sublocation_b, 10.0)
        self._create_quant(self.product, self.nested_sublocation, 10.0)

        # Freeze only sublocation_a (not the parent WH/Stock)
        self.stock_location.frozen = False
        self.sublocation_a.frozen = True

        # Verify frozen_parent_path is computed correctly
        self.assertFalse(self.stock_location.frozen_parent_path)
        self.assertTrue(self.sublocation_a.frozen_parent_path)
        self.assertFalse(self.sublocation_b.frozen_parent_path)
        self.assertTrue(self.nested_sublocation.frozen_parent_path)

        # Test: CAN update available quantity in WH/Stock (parent is not frozen)
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 5.0
        )

        # Test: CAN update available quantity in sublocation_b (sibling, not frozen)
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.sublocation_b, 5.0
        )

        # Test: CAN reserve stock in WH/Stock
        self.env["stock.quant"]._update_reserved_quantity(
            self.product, self.stock_location, 5.0
        )

        # Test: CAN reserve stock in sublocation_b
        self.env["stock.quant"]._update_reserved_quantity(
            self.product, self.sublocation_b, 5.0
        )

        # Test: CANNOT update available quantity in sublocation_a (frozen)
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_available_quantity(
                self.product, self.sublocation_a, 5.0
            )

        # Test: CANNOT update available quantity in nested_sublocation (parent frozen)
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_available_quantity(
                self.product, self.nested_sublocation, 5.0
            )

        # Test: CANNOT reserve stock in sublocation_a (frozen)
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_reserved_quantity(
                self.product, self.sublocation_a, 5.0
            )

        # Test: CANNOT reserve stock in nested_sublocation (parent frozen)
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_reserved_quantity(
                self.product, self.nested_sublocation, 5.0
            )

        # Unfreeze sublocation_a and verify operations are now allowed
        self.sublocation_a.frozen = False

        self.assertFalse(self.sublocation_a.frozen_parent_path)
        self.assertFalse(self.nested_sublocation.frozen_parent_path)

        # Should now be able to update quantities in previously frozen locations
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.sublocation_a, 5.0
        )
        self.env["stock.quant"]._update_reserved_quantity(
            self.product, self.nested_sublocation, 5.0
        )

    def test_skip_context_bypasses_freeze(self):
        """
        Test that when stock_location_freeze_skip context is True,
        operations are allowed even on frozen locations.
        """
        # Add stock to locations
        self._create_quant(self.product, self.stock_location, 10.0)
        self._create_quant(self.product, self.sublocation_a, 10.0)

        # Freeze the locations
        self.stock_location.frozen = True

        # Verify the locations are frozen
        self.assertTrue(self.stock_location.frozen_parent_path)
        self.assertTrue(self.sublocation_a.frozen_parent_path)

        # Without skip context, operations should fail
        with self.assertRaises(UserError):
            self.env["stock.quant"]._update_available_quantity(
                self.product, self.stock_location, 5.0
            )

        # With skip context, operations should succeed
        self.env["stock.quant"].with_context(
            stock_location_freeze_skip=True
        )._update_available_quantity(self.product, self.stock_location, 5.0)

        self.env["stock.quant"].with_context(
            stock_location_freeze_skip=True
        )._update_available_quantity(self.product, self.sublocation_a, 5.0)

        self.env["stock.quant"].with_context(
            stock_location_freeze_skip=True
        )._update_reserved_quantity(self.product, self.stock_location, 5.0)

        self.env["stock.quant"].with_context(
            stock_location_freeze_skip=True
        )._update_reserved_quantity(self.product, self.sublocation_a, 5.0)

    def test_action_assign_skips_frozen_sublocations(self):
        """
        Test that _action_assign on a stock.move does not reserve stock
        from frozen sub-locations, but does reserve after unfreezing.
        """
        # Only put stock in sublocation_a (not in WH/Stock itself)
        self._create_quant(self.product, self.sublocation_a, 5.0)

        # Create a stock move from WH/Stock to Customers
        move = self.env["stock.move"].create(
            {
                "name": "Test Move",
                "product_id": self.product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 5.0,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        move._action_confirm()

        # Freeze sublocation_a
        self.sublocation_a.frozen = True
        self.assertTrue(self.sublocation_a.frozen_parent_path)

        # Try to assign - should not reserve anything since stock is in frozen location
        move._action_assign()
        self.assertEqual(
            move.reserved_availability,
            0.0,
            "Should not reserve stock from frozen sublocation",
        )

        # Unfreeze sublocation_a
        self.stock_location.frozen = False
        self.sublocation_a.frozen = False
        self.assertFalse(self.sublocation_a.frozen_parent_path)

        # Try to assign again - should now reserve the stock
        move._action_assign()
        self.assertEqual(
            move.reserved_availability,
            5.0,
            "Should reserve stock after unfreezing sublocation",
        )

    def test_gather_only_filters_with_context(self):
        """
        Test that _gather only filters out frozen locations when the
        stock_location_freeze_gather context is True.
        """
        # Create stock in sublocation_a
        self._create_quant(self.product, self.sublocation_a, 10.0)

        # Without context, _gather returns quants even when unfrozen
        quants = self.env["stock.quant"]._gather(self.product, self.sublocation_a)
        self.assertEqual(len(quants), 1)
        self.assertEqual(quants.quantity, 10.0)

        # Freeze sublocation_a
        self.sublocation_a.frozen = True
        self.assertTrue(self.sublocation_a.frozen_parent_path)

        # Without context, _gather still returns quants (no filtering)
        quants = self.env["stock.quant"]._gather(self.product, self.sublocation_a)
        self.assertEqual(
            len(quants), 1, "_gather without context should return all quants"
        )

        # With stock_location_freeze_gather context, _gather filters out frozen
        # locations
        quants = (
            self.env["stock.quant"]
            .with_context(stock_location_freeze_gather=True)
            ._gather(self.product, self.sublocation_a)
        )
        self.assertEqual(
            len(quants), 0, "_gather with context should filter frozen locations"
        )

    def test_check_can_be_used_returns_false_for_frozen(self):
        """
        Test that _check_can_be_used returns False for frozen locations,
        preventing them from being used in putaway rules.
        """
        # Create stock in sublocation_a
        self._create_quant(self.product, self.sublocation_a, 10.0)

        self.stock_location.frozen = False
        self.sublocation_a.frozen = False
        self.assertFalse(self.sublocation_a.frozen_parent_path)

        # Unfrozen location should return True
        self.assertTrue(self.sublocation_a._check_can_be_used(self.product, quantity=1))

        # Freeze the location
        self.sublocation_a.frozen = True

        # Frozen location should return False
        self.assertFalse(
            self.sublocation_a._check_can_be_used(self.product, quantity=1)
        )

        # With skip context, should return True again
        self.assertTrue(
            self.sublocation_a.with_context(
                stock_location_freeze_skip=True
            )._check_can_be_used(self.product)
        )

    def test_gather_skip_context_bypasses_filter(self):
        """
        Test that stock_location_freeze_skip bypasses _gather filtering
        even when stock_location_freeze_gather is True.
        """
        self._create_quant(self.product, self.sublocation_a, 10.0)

        # Freeze the location
        self.sublocation_a.frozen = True

        # With only gather context, should filter out frozen locations
        quants = (
            self.env["stock.quant"]
            .with_context(stock_location_freeze_gather=True)
            ._gather(self.product, self.sublocation_a)
        )
        self.assertEqual(len(quants), 0)

        # With both gather and skip context, should NOT filter
        quants = (
            self.env["stock.quant"]
            .with_context(
                stock_location_freeze_gather=True,
                stock_location_freeze_skip=True,
            )
            ._gather(self.product, self.sublocation_a)
        )
        self.assertEqual(len(quants), 1)
