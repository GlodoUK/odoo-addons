# ruff: noqa: E501
from odoo.tests import Form, tagged

from .common import ProductConformityCommon


@tagged("post_install", "-at_install")
class TestProductConformityBackorder(ProductConformityCommon):
    """
    Test that _check_conformity_quantity runs correctly through the
    Create Backorder and No Backorder backorder wizard flow
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_tmpl_unit.product_variant_id.conformity_enabled = True

    def _do_backorder_wizard(self, production_id, create_backorder=True):
        res = production_id.button_mark_done()

        # button_mark_done should return a wizard action when under-produced
        self.assertTrue(
            isinstance(res, dict)
            and res.get("res_model") == "mrp.production.backorder",
            f"Expected backorder wizard action, got {res}",
        )

        wizard = Form(
            self.env["mrp.production.backorder"].with_context(**res["context"])
        ).save()

        if create_backorder:
            return wizard.action_backorder()

        return wizard.action_close_mo()

    def test_create_backorder_01(self):
        """
        Conformity Quantity = Produced Quantity = 100.0
        Production Quantity = 105.0
        Conformity alert must be created
        """
        production_id = self.env["mrp.production"].create(
            {
                "product_id": self.product_tmpl_unit.product_variant_id.id,
                "product_qty": 105.0,
            }
        )

        production_id.action_confirm()

        production_id.qty_producing = 100.0

        self._do_backorder_wizard(production_id, create_backorder=True)

        self.assertEqual(production_id.state, "done", "The production should be done!")

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            1,
            f"There should be one alert for {self.product_tmpl_unit.product_variant_id.name}",
        )

    def test_create_backorder_02(self):
        """
        Conformity Quantity = 100.0 < Produced Quantity = 102.0
        Production Quantity = 105.0
        Conformity alert must be created
        """
        production_id = self.env["mrp.production"].create(
            {
                "product_id": self.product_tmpl_unit.product_variant_id.id,
                "product_qty": 105.0,
            }
        )

        production_id.action_confirm()

        production_id.qty_producing = 102.0

        self._do_backorder_wizard(production_id, create_backorder=True)

        self.assertEqual(production_id.state, "done", "The production should be done!")

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            1,
            f"There should be one alert for {self.product_tmpl_unit.product_variant_id.name}",
        )

    def test_create_backorder_03(self):
        """
        Conformity Quantity = 100.0 > Produced Quantity = 50.0
        Production Quantity = 105.0
        Conformity alert shouldn't be created
        """
        production_id = self.env["mrp.production"].create(
            {
                "product_id": self.product_tmpl_unit.product_variant_id.id,
                "product_qty": 105.0,
            }
        )

        production_id.action_confirm()

        production_id.qty_producing = 50.0

        self._do_backorder_wizard(production_id, create_backorder=True)

        self.assertEqual(production_id.state, "done", "The production should be done!")

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            0,
            f"There should be no alerts for {self.product_tmpl_unit.product_variant_id.name}",
        )

    def test_no_backorder_01(self):
        """
        Conformity Quantity = 100.0 = Produced Quantity = 100.0
        Production Quantity = 105.0
        Conformity alert must be created
        """
        production_id = self.env["mrp.production"].create(
            {
                "product_id": self.product_tmpl_unit.product_variant_id.id,
                "product_qty": 105.0,
            }
        )

        production_id.action_confirm()

        production_id.qty_producing = 100.0

        self._do_backorder_wizard(production_id, create_backorder=False)

        self.assertEqual(production_id.state, "done", "The production should be done!")

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            1,
            f"There should be one alert for {self.product_tmpl_unit.product_variant_id.name}",
        )

    def test_no_backorder_02(self):
        """
        Conformity Quantity = 100.0 < Produced Quantity = 102.0
        Production Quantity = 105.0
        Conformity alert must be created
        """
        production_id = self.env["mrp.production"].create(
            {
                "product_id": self.product_tmpl_unit.product_variant_id.id,
                "product_qty": 105.0,
            }
        )

        production_id.action_confirm()

        production_id.qty_producing = 102.0

        self._do_backorder_wizard(production_id, create_backorder=False)

        self.assertEqual(production_id.state, "done", "The production should be done!")

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            1,
            f"There should be one alert for {self.product_tmpl_unit.product_variant_id.name}",
        )

    def test_no_backorder_03(self):
        """
        Conformity Quantity = 100.0 > Produced Quantity = 50.0
        Production Quantity = 105.0
        Conformity alert shouldn't be created
        """
        production_id = self.env["mrp.production"].create(
            {
                "product_id": self.product_tmpl_unit.product_variant_id.id,
                "product_qty": 105.0,
            }
        )

        production_id.action_confirm()

        production_id.qty_producing = 50.0

        self._do_backorder_wizard(production_id, create_backorder=False)

        self.assertEqual(production_id.state, "done", "The production should be done!")

        self.assertEqual(
            self._alert_count(self.product_tmpl_unit.product_variant_id),
            0,
            f"There should be no alerts for {self.product_tmpl_unit.product_variant_id.name}",
        )
