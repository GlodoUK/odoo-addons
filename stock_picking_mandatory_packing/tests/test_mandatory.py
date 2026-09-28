from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase


class TestMandatoryPacking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.picking_type_in = cls.warehouse.in_type_id
        cls.picking_type_int = cls.warehouse.int_type_id
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )

    def _make_picking(self, picking_type):
        return self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": picking_type.default_location_dest_id.id,
            }
        )

    def _add_move_line(self, picking, result_package=False):
        self.env["stock.move.line"].create(
            {
                "picking_id": picking.id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "qty_done": 1.0,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
                "result_package_id": result_package.id if result_package else False,
            }
        )

    def test_constrains_allows_outgoing(self):
        self.picking_type_out.must_be_packed = True

    def test_constrains_allows_incoming(self):
        self.picking_type_in.must_be_packed = True

    def test_constrains_allows_internal(self):
        self.picking_type_int.must_be_packed = True

    def test_constrains_rejects_non_standard_code(self):
        invalid_type = self.env["stock.picking.type"].search(
            [("code", "not in", ["incoming", "outgoing", "internal"])], limit=1
        )
        if not invalid_type:
            self.skipTest("No picking type with a non-standard code is installed")
        with self.assertRaises(ValidationError):
            invalid_type.must_be_packed = True

    def _sanity_check(self, picking):
        """Call _sanity_check with the parent implementation stubbed out so we
        only exercise this module's logic in isolation."""
        with patch(
            "odoo.addons.stock.models.stock_picking.StockPicking._sanity_check",
            return_value=None,
        ):
            picking._sanity_check()

    def test_no_error_when_must_be_packed_false_and_no_package(self):
        self.picking_type_out.must_be_packed = False
        picking = self._make_picking(self.picking_type_out)
        self._add_move_line(picking)
        self._sanity_check(picking)  # must not raise

    def test_no_error_when_must_be_packed_true_and_all_lines_packaged(self):
        self.picking_type_out.must_be_packed = True
        picking = self._make_picking(self.picking_type_out)
        package = self.env["stock.package"].create({})
        self._add_move_line(picking, result_package=package)
        self._sanity_check(picking)  # must not raise

    def test_error_when_must_be_packed_true_and_lines_without_package(self):
        self.picking_type_out.must_be_packed = True
        picking = self._make_picking(self.picking_type_out)
        self._add_move_line(picking)
        with self.assertRaises(UserError):
            self._sanity_check(picking)

    def test_error_only_for_unpackaged_lines(self):
        """Mix of packed/unpacked lines - the unpacked one triggers the error."""
        self.picking_type_out.must_be_packed = True
        picking = self._make_picking(self.picking_type_out)
        package = self.env["stock.package"].create({})
        self._add_move_line(picking, result_package=package)
        self._add_move_line(picking)  # no package
        with self.assertRaises(UserError):
            self._sanity_check(picking)

    def test_no_error_when_must_be_packed_false_even_with_no_lines(self):
        self.picking_type_out.must_be_packed = False
        picking = self._make_picking(self.picking_type_out)
        self._sanity_check(picking)  # must not raise
