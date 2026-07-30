from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPackageConsolidation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Package Product",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.package_type = cls.env["stock.package.type"].create(
            {
                "name": "Euro Package",
                "can_be_consolidated": True,
            }
        )
        cls.env["consolidation.package.capacity"].create(
            {
                "product_id": cls.product.id,
                "package_type_id": cls.package_type.id,
                "max_qty": 100.0,
            }
        )
        cls.location = cls.env.ref("stock.stock_location_stock")
        cls.shelf_category = cls.env["stock.storage.category"].create(
            {
                "name": "Shelf",
                "capacity_ids": [
                    Command.create(
                        {
                            "package_type_id": cls.package_type.id,
                            "quantity": 2,
                        }
                    )
                ],
            }
        )
        cls.shelf1, cls.shelf2 = cls.env["stock.location"].create(
            [
                {
                    "name": name,
                    "usage": "internal",
                    "location_id": cls.location.id,
                    "storage_category_id": cls.shelf_category.id,
                }
                for name in ("Shelf 1", "Shelf 2")
            ]
        )
        cls.package_a, cls.package_b, cls.package_c = cls.env["stock.package"].create(
            [
                {"name": name, "package_type_id": cls.package_type.id}
                for name in ("PKG-A", "PKG-B", "PKG-C")
            ]
        )

    def _add_stock(self, package, qty, product=None, location=None):
        self.env["stock.quant"]._update_available_quantity(
            product or self.product, location or self.location, qty, package_id=package
        )
        package.invalidate_recordset()

    def _consolidate(self, packages, target):
        wizard = self.env["consolidation.package.wizard"].create(
            {
                "package_ids": [Command.set(packages.ids)],
                "target_package_id": target.id,
            }
        )
        action = wizard.action_consolidate()
        return self.env["stock.picking"].browse(action["res_id"])

    def test_package_capacity_and_levels(self):
        self._add_stock(self.package_a, 30)
        self.assertEqual(
            self.env["consolidation.package.capacity"]._get_capacity(
                self.product, self.package_type
            ),
            100.0,
        )
        self.assertEqual(self.package_a.package_product_id, self.product)
        self.assertEqual(self.package_a.content_qty, 30)
        self.assertEqual(self.package_a.capacity_qty, 100)
        self.assertEqual(self.package_a.remaining_qty, 70)

    def test_consolidation_candidates(self):
        # A+B fit (30+40<=100), C pairs with nothing; finder is global so scope it.
        self._add_stock(self.package_a, 30)
        self._add_stock(self.package_b, 40, location=self.shelf1)
        self._add_stock(self.package_c, 90)
        candidates = self.env["stock.package"]._find_consolidation_candidates()
        self.assertEqual(
            candidates.filtered(lambda p: p.package_product_id == self.product),
            self.package_a + self.package_b,
        )

    def test_consolidation_screen(self):
        self._add_stock(self.package_a, 30)
        self._add_stock(self.package_b, 40)

        action = self.env["consolidation.package.line"].action_open()
        self.assertEqual(action["res_model"], "consolidation.package.line")
        self.assertEqual(action["context"]["group_by"], ["product_id"])
        # The screen is global; assert on this test's product only.
        lines = self.env["consolidation.package.line"].search(
            action["domain"] + [("product_id", "=", self.product.id)]
        )
        self.assertEqual(lines.package_id, self.package_a + self.package_b)

        wizard_action = lines.action_consolidate()
        self.assertEqual(wizard_action["res_model"], "consolidation.package.wizard")
        package_ids = wizard_action["context"]["default_package_ids"][0][2]
        self.assertEqual(set(package_ids), set(lines.package_id.ids))
        with self.assertRaises(UserError):
            lines[:1].action_consolidate()

        # The product group row button targets the same packages.
        group_action = self.product.action_consolidate_group()
        self.assertEqual(
            set(group_action["context"]["default_package_ids"][0][2]),
            set(lines.package_id.ids),
        )

    def test_consolidation_end_to_end(self):
        # Source A sits in another location of the warehouse than target B.
        self._add_stock(self.package_a, 30, location=self.shelf1)
        self._add_stock(self.package_b, 40)
        picking = self._consolidate(self.package_a + self.package_b, self.package_b)

        # A reserved work order is raised; nothing has moved yet.
        self.assertEqual(picking.picking_type_id.code, "internal")
        self.assertNotEqual(picking.state, "done")
        line = picking.move_line_ids
        self.assertEqual(line.package_id, self.package_a)
        self.assertEqual(line.result_package_id, self.package_b)
        self.assertEqual(line.quantity, 30)
        self.assertEqual(line.location_id, self.shelf1)
        self.assertEqual(line.location_dest_id, self.location)
        (self.package_a + self.package_b).invalidate_recordset()
        self.assertEqual(self.package_a.reserved_qty, 30)
        self.assertEqual(self.package_b.content_qty, 40)

        # Validating merges A into B and empties A.
        picking.move_ids.picked = True
        picking.button_validate()
        (self.package_a + self.package_b).invalidate_recordset()
        self.assertEqual(self.package_b.content_qty, 70)
        self.assertEqual(self.package_a.content_qty, 0)

    def test_consolidation_guards(self):
        other = self.env["product.product"].create(
            {"name": "Other", "type": "consu", "is_storable": True}
        )
        self._add_stock(self.package_a, 10)
        self._add_stock(self.package_b, 10, product=other)
        with self.assertRaises(UserError, msg="mixed products must be refused"):
            self._consolidate(self.package_a + self.package_b, self.package_a)

        self._add_stock(self.package_c, 40)
        self.env["stock.quant"]._update_reserved_quantity(
            self.product, self.location, 5, package_id=self.package_a
        )
        self.package_a.invalidate_recordset()
        with self.assertRaises(UserError, msg="reserved source must be refused"):
            self._consolidate(self.package_a + self.package_c, self.package_c)

    def test_location_slots_and_underfilled_finder(self):
        self._add_stock(self.package_a, 30, location=self.shelf1)
        self._add_stock(self.package_b, 40, location=self.shelf2)
        self._add_stock(self.package_c, 50, location=self.shelf2)
        self.assertEqual(self.shelf1.package_capacity, 2)
        self.assertEqual(self.shelf1.package_count, 1)
        self.assertEqual(self.shelf1.free_package_slots, 1)

        underfilled = self.env["stock.location"]._find_underfilled_package_locations()
        # Shelf 1 holds 1 of 2; shelf 2 is full; empty locations never qualify.
        self.assertIn(self.shelf1, underfilled)
        self.assertNotIn(self.shelf2, underfilled)

    def test_relocation_screen(self):
        self._add_stock(self.package_a, 30, location=self.shelf1)
        self._add_stock(self.package_b, 40, location=self.shelf2)

        action = self.env["consolidation.location.line"].action_open()
        self.assertEqual(action["res_model"], "consolidation.location.line")
        self.assertEqual(action["context"]["group_by"], ["product_id"])
        # The screen is global; assert on this test's product only.
        lines = self.env["consolidation.location.line"].search(
            action["domain"] + [("product_id", "=", self.product.id)]
        )
        self.assertEqual(lines.package_id, self.package_a + self.package_b)

        wizard_action = lines.action_relocate()
        self.assertEqual(wizard_action["res_model"], "consolidation.location.wizard")

        # The product group row button targets the same packages.
        group_action = self.product.action_relocate_group()
        self.assertEqual(
            set(group_action["context"]["default_package_ids"][0][2]),
            set(lines.package_id.ids),
        )

    def test_relocation_end_to_end(self):
        self._add_stock(self.package_a, 30, location=self.shelf1)
        self._add_stock(self.package_b, 40, location=self.shelf2)
        wizard = self.env["consolidation.location.wizard"].create(
            {
                "package_ids": [Command.set(self.package_a.ids)],
                "dest_location_id": self.shelf2.id,
            }
        )
        action = wizard.action_relocate()
        picking = self.env["stock.picking"].browse(action["res_id"])

        # The whole package moves: same source and result package.
        line = picking.move_line_ids
        self.assertEqual(line.package_id, self.package_a)
        self.assertEqual(line.result_package_id, self.package_a)
        self.assertEqual(line.location_id, self.shelf1)
        self.assertEqual(line.location_dest_id, self.shelf2)

        picking.move_ids.picked = True
        picking.button_validate()
        self.package_a.invalidate_recordset()
        self.assertEqual(self.package_a.location_id, self.shelf2)
        self.assertEqual(self.package_a.content_qty, 30)
        self.assertEqual(self.shelf2.package_count, 2)

    def test_relocation_guards(self):
        self._add_stock(self.package_a, 30, location=self.shelf1)
        self._add_stock(self.package_b, 40, location=self.shelf2)
        self._add_stock(self.package_c, 50, location=self.shelf2)

        # Shelf 2 is full: not offered as a destination, and refused if forced.
        wizard = self.env["consolidation.location.wizard"].create(
            {
                "package_ids": [Command.set(self.package_a.ids)],
                "dest_location_id": self.shelf2.id,
            }
        )
        self.assertNotIn(self.shelf2, wizard.allowed_dest_location_ids)
        with self.assertRaises(UserError, msg="full destination must be refused"):
            wizard.action_relocate()

        self.env["stock.quant"]._update_reserved_quantity(
            self.product, self.shelf1, 10, package_id=self.package_a
        )
        self.package_a.invalidate_recordset()
        with self.assertRaises(UserError, msg="reserved package must be refused"):
            wizard.action_relocate()
