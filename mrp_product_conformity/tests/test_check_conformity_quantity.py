# ruff: noqa: E501
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged

from .common import ProductConformityCommon


@tagged("post_install", "-at_install")
class TestButtonMarkDone(ProductConformityCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_tmpl_dozen.product_variant_id.conformity_enabled = False
        cls.product_tmpl_unit.product_variant_id.conformity_enabled = True

    def test_button_mark_done_handle_done(self):
        """
        Conformity Quantity = 100.0
        Production A Quantity = 50.0
        Production B Quantity = 40.0

        button_mark_done on Production A
        button_mark_done on Production A + Production B

        Production A should not be double counted
        and a conformity alert should not be created
        """

        done_production_id = self._create_production_done(
            self.product_tmpl_unit.product_variant_id,
            50,
        )

        self.assertEqual(
            done_production_id.state,
            "done",
        )

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            0,
            f"There should be no alerts for {self.product_tmpl_unit.product_variant_id.name}",
        )

        new_production_id = self._create_production(
            self.product_tmpl_unit.product_variant_id,
            40,
        )

        new_production_id.qty_producing = 40.0

        (done_production_id | new_production_id).button_mark_done()

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            0,
            f"There should be no alerts for {self.product_tmpl_unit.product_variant_id.name}",
        )

    def test_conformity_enabled(self):
        """
        Conformity Quantity = 100.0
        Production A Quantity = 100.0
        Production B Quantity = 100.0

        Production A has a product with conformity_enabled
        Production B has a product without conformity_enabled

        Production A should create an alert, Production B should not create an alert
        """
        self._create_production_done(self.product_tmpl_unit.product_variant_id, 100.0)

        self._create_production_done(self.product_tmpl_dozen.product_variant_id, 100.0)

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            1,
            f"There should be no alerts for {self.product_tmpl_unit.product_variant_id.name}",
        )

        self.assertEqual(
            self._alert_count(self.product_tmpl_dozen.product_variant_id),
            0,
            f"There should be no alerts for {self.product_tmpl_unit.product_variant_id.name}",
        )

    def test_multiple_production_same_product(self):
        production_id_1 = self._create_production(
            self.product_tmpl_unit.product_variant_id, 50.0
        )

        production_id_1.qty_producing = production_id_1.product_qty

        production_id_2 = self._create_production(
            self.product_tmpl_unit.product_variant_id, 50.0
        )

        production_id_2.qty_producing = production_id_2.product_qty

        (production_id_1 | production_id_2).button_mark_done()

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            1,
            f"There should be one alert for {self.product_tmpl_unit.product_variant_id.name}",
        )

    def test_quantity_below_threshold_no_alert(self):
        self._create_production_done(self.product_tmpl_unit.product_variant_id, 80.0)

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            0,
            f"There should be no alerts for {self.product_tmpl_unit.product_variant_id.name}",
        )

    def test_production_outside_conformity_window_excluded(self):
        # Create MO with date_finished before the conformity start date
        past_date = fields.Datetime.now() - relativedelta(days=30)

        self._create_production_done(
            self.product_tmpl_unit.product_variant_id,
            100,
            date_finished=past_date,
        )

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            0,
            f"There should be no alerts for {self.product_tmpl_unit.product_variant_id.name}",
        )

    def test_uom_conversion(self):
        # Change product UOM to units so conformity_quantity is in units
        self.product_tmpl_dozen.product_variant_id.write(
            {
                "conformity_enabled": True,
                "conformity_quantity": 10.0,
                "uom_id": self.uom_unit.id,
            }
        )

        # Create production with dozen UOM: 1 Dozen = 12 Units
        production_id = self.env["mrp.production"].create(
            {
                "product_id": self.product_tmpl_dozen.product_variant_id.id,
                "product_uom_id": self.uom_dozen.id,
                "product_qty": 1.0,
            }
        )

        production_id.action_confirm()
        production_id.qty_producing = production_id.product_qty
        production_id.button_mark_done()

        self.assertEqual(
            self._alert_count(self.product_dozen),
            1,
            f"There should be one alert for {self.product_dozen}",
        )
