from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMod(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.warehouse = cls.env["stock.warehouse"].create(
            {"name": "Noop Test Warehouse", "code": "NOP"}
        )
        cls.stock_location = cls.warehouse.lot_stock_id

        cls.product = cls.env["product.product"].create(
            {"name": "Noop Test Product", "is_storable": True}
        )

        cls.noop_route = cls.env.ref("stock_rule_action_noop.stock_route_noop")
        cls.noop_rule = cls.env["stock.rule"].create(
            {
                "name": "Noop Rule",
                "action": "noop",
                "route_id": cls.noop_route.id,
                "location_dest_id": cls.stock_location.id,
                "picking_type_id": cls.warehouse.in_type_id.id,
            }
        )

    def _make_procurement(self, values=None):
        Procurement = self.env["stock.rule"].Procurement
        return Procurement(
            product_id=self.product,
            product_qty=1.0,
            product_uom=self.product.uom_id,
            location_id=self.stock_location,
            name="Test procurement",
            origin="test",
            company_id=self.env.company,
            values=dict({"route_ids": self.noop_route}, **(values or {})),
        )

    def test_noop_creates_no_moves(self):
        move_count_before = self.env["stock.move"].search_count([])
        self.env["stock.rule"].run([self._make_procurement()])
        self.assertEqual(self.env["stock.move"].search_count([]), move_count_before)

    def test_noop_resets_downstream_procure_method(self):
        downstream_move = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 1.0,
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "procure_method": "make_to_order",
                "picking_type_id": self.warehouse.out_type_id.id,
            }
        )

        self.env["stock.rule"].run(
            [self._make_procurement({"move_dest_ids": downstream_move})]
        )

        self.assertEqual(downstream_move.procure_method, "make_to_stock")
