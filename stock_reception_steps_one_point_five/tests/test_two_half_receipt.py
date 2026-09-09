from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTwoHalfReceipt(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].create(
            {
                "name": "Two And A Half",
                "code": "THS",
                "reception_steps": "two_half_step",
            }
        )
        cls.input_loc = cls.warehouse.wh_input_stock_loc_id
        cls.qc_loc = cls.warehouse.wh_qc_stock_loc_id
        cls.stock_loc = cls.warehouse.lot_stock_id

    def _active_reception_rules(self):
        return self.warehouse.reception_route_id.rule_ids.filtered("active")

    def _auto_store_rules(self):
        return self._active_reception_rules().filtered(
            lambda r: (
                r.location_dest_id == self.stock_loc
                and r.location_src_id in (self.input_loc | self.qc_loc)
            )
        )

    def test_quality_control_is_the_landing_area(self):
        # Receipts land in Input and are automatically routed on to Quality
        # Control, so both locations stay active.
        self.assertTrue(self.input_loc.active)
        self.assertTrue(self.qc_loc.active)
        self.assertEqual(
            self.warehouse.in_type_id.default_location_dest_id, self.input_loc
        )

    def test_input_to_quality_control_is_automatic(self):
        # The first two legs of the three-step receipt are untouched.
        qc_rule = self._active_reception_rules().filtered(
            lambda r: (
                r.location_src_id == self.input_loc
                and r.location_dest_id == self.qc_loc
            )
        )
        self.assertTrue(
            qc_rule,
            "A two-and-a-half-step receipt must keep the Input -> Quality Control rule",
        )

    def test_no_automatic_store_move(self):
        # Nothing automatically moves goods into Stock: the manual transfer is
        # the whole point of the two-and-a-half-step receipt.
        self.assertFalse(
            self._auto_store_rules(),
            "A two-and-a-half-step receipt must not generate a rule into Stock",
        )

    def test_quality_control_operation_type_is_active(self):
        # The automatic Input -> Quality Control leg needs its operation type.
        qc_type = self.warehouse.qc_type_id
        self.assertTrue(qc_type.active)
        self.assertEqual(qc_type.default_location_src_id, self.input_loc)
        self.assertEqual(qc_type.default_location_dest_id, self.qc_loc)

    def test_storage_operation_type_targets_quality_control_to_stock(self):
        # The operator uses the Storage operation type for the manual move.
        store_type = self.warehouse.store_type_id
        self.assertTrue(store_type.active)
        self.assertEqual(store_type.default_location_src_id, self.qc_loc)
        self.assertEqual(store_type.default_location_dest_id, self.stock_loc)

    def test_config_survives_rewrite(self):
        # Re-triggering the warehouse machinery (e.g. renaming) must not lose
        # the custom routing.
        self.warehouse.write({"name": "Two And A Half (edited)"})
        self.assertEqual(self.warehouse.reception_steps, "two_half_step")
        self.assertEqual(
            self.warehouse.in_type_id.default_location_dest_id, self.input_loc
        )
        self.assertTrue(self.qc_loc.active)
        self.assertTrue(self.warehouse.qc_type_id.active)
        self.assertFalse(self._auto_store_rules())

    def test_switch_from_three_steps(self):
        # Switching an existing three-step warehouse over drops the automatic
        # store move but keeps Quality Control in place.
        warehouse = self.env["stock.warehouse"].create(
            {
                "name": "Switcher",
                "code": "SWT",
                "reception_steps": "three_steps",
            }
        )
        store_rule = warehouse.reception_route_id.rule_ids.filtered(
            lambda r: (
                r.active
                and r.location_src_id == warehouse.wh_qc_stock_loc_id
                and r.location_dest_id == warehouse.lot_stock_id
            )
        )
        self.assertTrue(store_rule)

        warehouse.write({"reception_steps": "two_half_step"})
        self.assertTrue(warehouse.wh_qc_stock_loc_id.active)
        self.assertTrue(warehouse.qc_type_id.active)
        self.assertEqual(
            warehouse.store_type_id.default_location_src_id,
            warehouse.wh_qc_stock_loc_id,
        )
        remaining = warehouse.reception_route_id.rule_ids.filtered(
            lambda r: r.active and r.location_dest_id == warehouse.lot_stock_id
        )
        self.assertFalse(remaining)
