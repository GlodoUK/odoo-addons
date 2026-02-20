from odoo.tests import TransactionCase


class StockQuantRemovalStrategy(TransactionCase):
    def setUp(self):
        super().setUp()
        self.least_package_strategy = self.env.ref(
            "backport_stock_removal_least_packages.removal_least_packages"
        )
        self.product = self.env["product.product"].create(
            {
                "name": "Product",
                "type": "product",
            }
        )
        self.product.categ_id.removal_strategy_id = self.least_package_strategy.id
        self.stock_location = self.env["stock.location"].create(
            {
                "name": "stock_location",
                "usage": "internal",
            }
        )

    def _generate_data(self, packages_data):
        move = self.env["stock.move"].create(
            {
                "name": "Test Least Package",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "location_id": self.ref("stock.stock_location_suppliers"),
                "location_dest_id": self.stock_location.id,
            }
        )
        move._action_confirm()

        ml_vals_list = []
        ml_common_vals = {
            "move_id": move.id,
            "product_id": self.product.id,
            "product_uom_id": self.product.uom_id.id,
            "location_id": self.ref("stock.stock_location_suppliers"),
            "location_dest_id": self.stock_location.id,
        }

        packages = self.env["stock.quant.package"].create(
            [{}] * sum(p[1] for p in packages_data if p[0])
        )
        for package_size, number_of_packages in packages_data:
            if not package_size:
                ml_vals_list.append(
                    dict(
                        **ml_common_vals,
                        **{
                            "product_uom_qty": number_of_packages,
                        },
                    )
                )
                continue
            for _dummy in range(number_of_packages):
                package = packages[0]
                packages = packages[1:]
                ml_vals_list.append(
                    dict(
                        **ml_common_vals,
                        **{
                            "product_uom_qty": package_size,
                            "result_package_id": package.id,
                        },
                    )
                )
        self.env["stock.move.line"].create(ml_vals_list)
        move._set_quantities_to_reservation()
        move._action_done()

    def test_least_package_removal_strategy_priority_to_package(self):
        """
        Tests the least package removal strategy in a use case where only one package
        needs to be selected.
        It should only return the quantity of a single size 1000 package.
        """
        packages_data = [
            (False, 2000),
            (5, 10),
            (50, 10),
            (1000, 2),
        ]
        self._generate_data(packages_data)

        # Out 1000 should selecte a package with 1000 units inside
        move = self.env["stock.move"].create(
            {
                "name": "Test Least Package",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.ref("stock.stock_location_customers"),
                "product_uom_qty": 1000,
            }
        )
        move._action_confirm()
        move._action_assign()
        self.assertEqual(len(move.move_line_ids), 1, "Only one pack could be use")
        self.assertTrue(
            move.move_line_ids.package_id,
            "A package should be selected, priority to package even if there is enough"
            " quantity without package",
        )

    def test_least_package_removal_strategy_simple_usecase(self):
        """
        Tests the least package removal strategy in a simple "typical" use case.
        It should return a minimal exact matching for the requested quantity.
        """
        packages_data = [
            (5, 10),
            (50, 10),
            (1000, 2),
        ]
        self._generate_data(packages_data)

        # Out 1000 should select a package with 1000 units inside
        move = self.env["stock.move"].create(
            {
                "name": "Test Least Package",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.ref("stock.stock_location_customers"),
                "product_uom_qty": 1280,
            }
        )
        move._action_confirm()
        move._action_assign()
        self.assertEqual(len(move.move_line_ids), 12)
        self.assertRecordValues(
            move.move_line_ids,
            [{"product_uom_qty": 1000}]
            + [{"product_uom_qty": 50}] * 5
            + [{"product_uom_qty": 5}] * 6,
        )

    # FIXME
    # def test_least_package_removal_strategy_not_possible(self):
    #     """
    #     Tests the least package removal strategy in the case where an exact matching
    #     of packages is not possible for the requested amount.
    #     It should return the best leaf from the A* search.
    #     """
    #     packages_data = [
    #         (False, 2),
    #         (5, 2),
    #         (10, 5),
    #     ]
    #     self._generate_data(packages_data)
    #
    #     move = self.env['stock.move'].create({
    #         'name': 'Test Least Package',
    #         'product_id': self.product.id,
    #         'product_uom': self.product.uom_id.id,
    #         'location_id': self.stock_location.id,
    #         'location_dest_id': self.ref('stock.stock_location_customers'),
    #         'product_uom_qty': 13,
    #     })
    #     move._action_confirm()
    #     move._action_assign()
    #     self.assertEqual(len(move.move_line_ids), 2)
    #     self.assertRecordValues(
    #         move.move_line_ids,
    #         [{'product_uom_qty': 10}] + [{'product_uom_qty': 3}]
    #     )
    #     # Make sure it selects the smallest possible package as best leaf.
    #     self.assertEqual(
    #         move.move_line_ids[1].package_id.quant_ids.quantity,
    #         5
    #     )

    # FIXME
    # def test_least_package_removal_strategy_not_enough(self):
    #     """
    #     Tests the least package removal strategy in the case where not enough quantity
    #     is available to fill the requested amount.
    #     It should just return all the quantities in the domain.
    #     """
    #     packages_data = [
    #         (False, 2),
    #         (5, 2),
    #         (10, 5),
    #     ]
    #     self._generate_data(packages_data)
    #
    #     move = self.env['stock.move'].create({
    #         'name': 'Test Least Package',
    #         'product_id': self.product.id,
    #         'product_uom': self.product.uom_id.id,
    #         'location_id': self.stock_location.id,
    #         'location_dest_id': self.ref('stock.stock_location_customers'),
    #         'product_uom_qty': 90,
    #     })
    #     move._action_confirm()
    #     move._action_assign()
    #     self.assertEqual(len(move.move_line_ids), 8)
    #     self.assertRecordValues(
    #         move.move_line_ids,
    #         [{'product_uom_qty': 2}] +
    #         [{'product_uom_qty': 10}] * 5 +
    #         [{'product_uom_qty': 5}] * 2
    #     )

    def test_clean_quant_after_package_move(self):
        """
        A product is at WH/Stock in a package PK. We deliver PK. The user should
        not find any quant at WH/Stock with PK anymore.
        """
        package = self.env["stock.quant.package"].create({})
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 1.0, package_id=package
        )

        move = self.env["stock.move"].create(
            {
                "name": "OUT 1 product",
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "product_uom": self.product.uom_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.ref("stock.stock_location_customers"),
            }
        )
        move._action_confirm()
        move._action_assign()
        move.move_line_ids.write(
            {
                "result_package_id": package.id,
                "product_uom_qty": 1,
            }
        )
        move._set_quantities_to_reservation()
        move._action_done()

        self.assertFalse(
            self.env["stock.quant"].search_count(
                [
                    ("product_id", "=", self.product.id),
                    ("package_id", "=", package.id),
                    ("location_id", "=", self.stock_location.id),
                ]
            )
        )
