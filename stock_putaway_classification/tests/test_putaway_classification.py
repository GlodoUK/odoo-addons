from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPutawayClassification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Classification = cls.env["product.classification"]
        cls.high = Classification.create({"name": "SPC High", "code": "SPC-H"})
        cls.medium = Classification.create({"name": "SPC Medium", "code": "SPC-M"})
        cls.low = Classification.create({"name": "SPC Low", "code": "SPC-L"})
        Location = cls.env["stock.location"]
        StorageCategory = cls.env["stock.storage.category"]
        cls.warehouse = cls.env["stock.warehouse"].create(
            {"name": "Putaway Classification WH", "code": "SPCWH"}
        )
        cls.stock = cls.warehouse.lot_stock_id
        cls.pick = Location.create({"name": "Pick", "location_id": cls.stock.id})
        cls.bulk = Location.create({"name": "Bulk", "location_id": cls.stock.id})
        cls.high_category = StorageCategory.create(
            {"name": "SPC Picking - High", "allow_new_product": "empty"}
        )
        cls.medium_category = StorageCategory.create(
            {"name": "SPC Picking - Medium", "allow_new_product": "empty"}
        )
        cls.bulk_category = StorageCategory.create(
            {"name": "SPC Bulk", "allow_new_product": "same"}
        )

        def _bin(name, parent, category):
            return Location.create(
                {
                    "name": name,
                    "location_id": parent.id,
                    "storage_category_id": category.id,
                }
            )

        cls.high_face_1 = _bin("SPC-H1", cls.pick, cls.high_category)
        cls.high_face_2 = _bin("SPC-H2", cls.pick, cls.high_category)
        cls.medium_face = _bin("SPC-M1", cls.pick, cls.medium_category)
        cls.bulk_bin = _bin("SPC-B1", cls.bulk, cls.bulk_category)

        Rule = cls.env["stock.putaway.rule"]
        rule_vals = [
            {
                "location_in_id": cls.stock.id,
                "location_out_id": cls.pick.id,
                "product_classification_id": classification.id,
                "sublocation": "closest_location",
                "storage_category_id": category.id,
            }
            for classification, category in (
                (cls.high, cls.high_category),
                (cls.medium, cls.medium_category),
            )
        ]
        # Catch-all first by sequence: classification rules must still win.
        rule_vals.insert(
            0,
            {
                "sequence": 0,
                "location_in_id": cls.stock.id,
                "location_out_id": cls.bulk.id,
                "sublocation": "closest_location",
                "storage_category_id": cls.bulk_category.id,
            },
        )
        Rule.create(rule_vals)

        cls.product = cls._product("SPC-TEST-HIGH", cls.high)
        cls.other_product = cls._product("SPC-TEST-HIGH-2", cls.high)

    @classmethod
    def _product(cls, code, classification=None):
        return cls.env["product.product"].create(
            {
                "name": code,
                "default_code": code,
                "is_storable": True,
                "product_classification_id": classification and classification.id,
            }
        )

    def _putaway(self, product, quantity=1):
        return self.stock._get_putaway_strategy(product, quantity=quantity)

    def _stock(self, product, location, quantity=5):
        self.env["stock.quant"]._update_available_quantity(product, location, quantity)

    def test_classified_product_goes_to_empty_face_of_its_class(self):
        self.assertEqual(self._putaway(self.product), self.high_face_1)

    def test_other_classification_goes_to_its_class(self):
        product = self._product("SPC-TEST-MEDIUM", self.medium)
        self.assertEqual(self._putaway(product), self.medium_face)

    def test_classification_without_rule_goes_to_bulk(self):
        product = self._product("SPC-TEST-LOW", self.low)
        self.assertEqual(self._putaway(product), self.bulk_bin)

    def test_unclassified_product_goes_to_bulk(self):
        product = self._product("SPC-TEST-NONE")
        self.assertEqual(self._putaway(product), self.bulk_bin)

    def test_product_with_a_face_goes_to_bulk(self):
        """A product keeps one pick face: while it has stock in Pick, new
        stock goes to bulk rather than a second face."""
        self._stock(self.product, self.high_face_1)
        self.assertEqual(self._putaway(self.product), self.bulk_bin)

    def test_occupied_face_is_skipped(self):
        self._stock(self.other_product, self.high_face_1)
        self.assertEqual(self._putaway(self.product), self.high_face_2)

    def test_face_with_incoming_stock_is_skipped(self):
        """Core "empty" only checks quants; a face another product is already
        being put away into is not empty."""
        move = self.env["stock.move"].create(
            {
                "product_id": self.other_product.id,
                "product_uom_qty": 1,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.high_face_1.id,
            }
        )
        move._action_confirm()
        move._action_assign()
        self.assertEqual(move.move_line_ids.location_dest_id, self.high_face_1)
        self.assertEqual(self._putaway(self.product), self.high_face_2)

    def test_product_rule_beats_classification(self):
        self.env["stock.putaway.rule"].create(
            {
                "location_in_id": self.stock.id,
                "location_out_id": self.medium_face.id,
                "product_id": self.product.id,
            }
        )
        self.assertEqual(self._putaway(self.product), self.medium_face)

    def test_template_mirrors_single_variant(self):
        template = self.product.product_tmpl_id
        self.assertEqual(template.product_classification_id, self.high)
        template.product_classification_id = self.low
        self.assertEqual(self.product.product_classification_id, self.low)

    def test_display_name_shows_code(self):
        self.assertEqual(self.high.display_name, "[SPC-H] SPC High")

    def _package(self, name, package_type):
        return self.env["stock.package"].create(
            {"name": name, "package_type_id": package_type.id}
        )

    def _putaway_package(self, package, product):
        return self.stock.with_context(products=product)._get_putaway_strategy(
            self.env["product.product"], package=package
        )

    def _sized_category(self, name, package_type):
        """A classification + pallet size category, as the bootstrap makes."""
        return self.env["stock.storage.category"].create(
            {
                "name": name,
                "allow_new_product": "empty",
                "only_listed_package_types": True,
                "capacity_ids": [
                    Command.create({"package_type_id": package_type.id, "quantity": 1})
                ],
            }
        )

    def test_package_type_rule_wins(self):
        """A package goes to a bin of its own size first, ahead of the
        classification's rule without a package type."""
        package_type = self.env["stock.package.type"].create(
            {"name": "SPC Pallet", "barcode": "SPC-PT-PALLET"}
        )
        self.high_face_2.storage_category_id = self._sized_category(
            "SPC Picking - High: Pallet", package_type
        )
        self.env["stock.putaway.rule"].create(
            {
                "location_in_id": self.stock.id,
                "location_out_id": self.pick.id,
                "product_classification_id": self.high.id,
                "package_type_ids": package_type.ids,
                "sublocation": "closest_location",
                "storage_category_id": self.high_face_2.storage_category_id.id,
            }
        )
        package = self._package("SPC-PACK", package_type)
        self.assertEqual(self._putaway_package(package, self.product), self.high_face_2)
        # Unpackaged stock still takes any face of its classification's rule.
        self.assertEqual(self._putaway(self.product), self.high_face_1)

    def test_only_listed_package_types(self):
        """A category with "Only Listed Package Types" refuses packages of
        any other type, but not unpackaged stock."""
        listed = self.env["stock.package.type"].create(
            {"name": "SPC Small Pallet", "barcode": "SPC-PT-SMALL"}
        )
        other = self.env["stock.package.type"].create(
            {"name": "SPC Tall Pallet", "barcode": "SPC-PT-TALL"}
        )
        sized = self._sized_category("SPC Picking - High: Small", listed)
        (self.high_face_1 | self.high_face_2).storage_category_id = sized
        self.env["stock.putaway.rule"].search(
            [("product_classification_id", "=", self.high.id)]
        ).storage_category_id = sized
        self.assertEqual(
            self._putaway_package(self._package("SPC-TALL", other), self.product),
            self.bulk_bin,
        )
        self.assertEqual(
            self._putaway_package(self._package("SPC-SMALL", listed), self.product),
            self.high_face_1,
        )
        self.assertEqual(self._putaway(self.product), self.high_face_1)
