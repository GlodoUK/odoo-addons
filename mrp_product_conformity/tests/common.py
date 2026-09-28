from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import TransactionCase


class ProductConformityCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")

        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

        cls.categ_id = cls.env["product.category"].create(
            {
                "name": "Test Categ",
            }
        )

        cls.product_tmpl_unit = cls.env["product.template"].create(
            {
                "name": "Test Product Unit",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.categ_id.id,
                "uom_id": cls.uom_unit.id,
            }
        )

        cls.product_tmpl_dozen = cls.env["product.template"].create(
            {
                "name": "Test Product Dozen",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.categ_id.id,
                "uom_id": cls.uom_dozen.id,
            }
        )

        cls.product_unit = cls.product_tmpl_unit.product_variant_id
        cls.product_dozen = cls.product_tmpl_dozen.product_variant_id

        cls.product_unit.conformity_start_date = fields.Datetime.now()
        cls.product_dozen.conformity_start_date = fields.Datetime.now()

    def _alert_count(self, product_id):
        product_id.ensure_one()

        return self.env["product.conformity.alert"].search_count(
            [
                ("product_id", "=", product_id.id),
                ("state", "=", "open"),
            ]
        )

    def _create_production(self, product_id, product_qty):
        product_id.ensure_one()

        production_id = self.env["mrp.production"].create(
            {
                "product_id": product_id.id,
                "product_uom_id": product_id.uom_id.id,
                "product_qty": product_qty,
            }
        )

        production_id.action_confirm()

        return production_id

    def _create_production_done(self, product_id, product_qty, date_finished=None):
        product_id.ensure_one()

        production_id = self._create_production(product_id, product_qty)

        production_id.qty_producing = production_id.product_qty

        if date_finished:
            with freeze_time(date_finished):
                production_id.button_mark_done()
        else:
            production_id.button_mark_done()

        return production_id
