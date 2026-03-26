from odoo.tests import TransactionCase


class TestAutoPutInPack(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")

        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "is_storable": True, "weight": 1.0}
        )
        cls.package_type = cls.env["stock.package.type"].create(
            {"name": "Test Box", "max_weight": 5.0}
        )

    def _create_picking(self, qty):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_in.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.supplier_location.id,
                            "location_dest_id": self.stock_location.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_line_ids.quantity = qty
        return picking

    def _create_wizard(self, picking):
        return self.env["stock.put.in.pack"].create(
            {
                "move_line_ids": [(6, 0, picking.move_line_ids.ids)],
                "package_type_id": self.package_type.id,
                "auto_put_in_pack": "auto",
            }
        )

    def test_with_capacity(self):
        """
        Fixed product capacity of 1 should split a line of qty 10 into 10 lines of
        qty 1.
        """
        self.env["stock.package.type.product.capacity"].create(
            {
                "package_type_id": self.package_type.id,
                "product_id": self.product.id,
                "quantity": 1.0,
            }
        )
        picking = self._create_picking(10)
        self._create_wizard(picking).action_put_in_pack()

        lines = picking.move_line_ids
        self.assertEqual(len(lines), 10)
        self.assertTrue(all(line.result_package_id for line in lines))
        self.assertTrue(all(line.quantity == 1.0 for line in lines))

    def test_by_weight(self):
        """
        Max weight 5 kg with product weight 1 kg should split qty 10 into 2 lines of
        qty 5.
        """
        picking = self._create_picking(10)
        self._create_wizard(picking).action_put_in_pack()

        lines = picking.move_line_ids
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(line.result_package_id for line in lines))
        self.assertTrue(all(line.quantity == 5.0 for line in lines))

    def test_by_volume(self):
        """
        Package 2×2×2 m³ with product volume 2 m³ (4 per package) should split qty 8
        into 2 lines of qty 4.
        """
        self.product.volume = 2.0
        self.package_type.write(
            {"packaging_length": 2.0, "width": 2.0, "height": 2.0, "max_weight": 0.0}
        )
        picking = self._create_picking(8)
        self._create_wizard(picking).action_put_in_pack()

        lines = picking.move_line_ids
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(line.result_package_id for line in lines))
        self.assertTrue(all(line.quantity == 4.0 for line in lines))

    def test_skip_existing_with_package(self):
        """Lines that already have a result_package_id must not be repacked."""
        picking = self._create_picking(10)
        existing_package = self.env["stock.package"].create({"name": "EXISTING"})
        picking.move_line_ids.result_package_id = existing_package

        self._create_wizard(picking).action_put_in_pack()

        self.assertTrue(
            all(
                line.result_package_id == existing_package
                for line in picking.move_line_ids
            )
        )
