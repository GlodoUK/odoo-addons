from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestOneHalfReceipt(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].create(
            {
                "name": "One And A Half",
                "code": "OHS",
                "reception_steps": "one_half_step",
            }
        )
        cls.input_loc = cls.warehouse.wh_input_stock_loc_id
        cls.stock_loc = cls.warehouse.lot_stock_id

    def _active_reception_rules(self):
        return self.warehouse.reception_route_id.rule_ids.filtered("active")

    def test_input_is_the_landing_area(self):
        # Input is active and receipts land there, not directly in Stock.
        self.assertTrue(self.input_loc.active)
        self.assertFalse(self.warehouse.wh_qc_stock_loc_id.active)
        self.assertEqual(
            self.warehouse.in_type_id.default_location_dest_id, self.input_loc
        )

    def test_no_automatic_store_move(self):
        # Nothing automatically moves goods from Input to Stock: the manual
        # transfer is the whole point of the one-and-a-half-step receipt.
        auto_store = self._active_reception_rules().filtered(
            lambda r: (
                r.location_src_id == self.input_loc
                and r.location_dest_id == self.stock_loc
            )
        )
        self.assertFalse(
            auto_store,
            "A one-and-a-half-step receipt must not generate an Input -> Stock rule",
        )

    def test_storage_operation_type_targets_input_to_stock(self):
        # The operator uses the Storage operation type for the manual move.
        store_type = self.warehouse.store_type_id
        self.assertTrue(store_type.active)
        self.assertEqual(store_type.default_location_src_id, self.input_loc)
        self.assertEqual(store_type.default_location_dest_id, self.stock_loc)

    def test_config_survives_rewrite(self):
        # Re-triggering the warehouse machinery (e.g. renaming) must not lose
        # the custom routing.
        self.warehouse.write({"name": "One And A Half (edited)"})
        self.assertEqual(self.warehouse.reception_steps, "one_half_step")
        self.assertEqual(
            self.warehouse.in_type_id.default_location_dest_id, self.input_loc
        )
        auto_store = self._active_reception_rules().filtered(
            lambda r: (
                r.location_src_id == self.input_loc
                and r.location_dest_id == self.stock_loc
            )
        )
        self.assertFalse(auto_store)
