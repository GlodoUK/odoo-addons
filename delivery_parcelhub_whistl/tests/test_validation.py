from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestValidation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_id = cls.env["res.partner"].create(
            {
                "name": "A",
            }
        )
        cls.carrier_id = cls._create_carrier("Whistl Test", delivery_type="whistl")
        cls.picking_id = cls.env["stock.picking"].create(
            {
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "partner_id": cls.partner_id.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "carrier_id": cls.carrier_id.id,
            }
        )

    @classmethod
    def _create_carrier(cls, name, **kwargs):
        carrier_product = cls.env["product.product"].create(
            {
                "name": f"product {name}",
                "type": "service",
            }
        )
        carrier_values = {"name": name, "product_id": carrier_product.id}
        carrier_values.update(kwargs)
        return cls.env["delivery.carrier"].create(carrier_values)

    def test_validation_name_fails(self):
        self.partner_id.name = "A" * 35
        with self.assertRaises(UserError):
            self.carrier_id._ensure_valid_shipping(self.picking_id)

    def test_validation_name_succeeds(self):
        self.partner_id.name = "A" * 32
        self.carrier_id._ensure_valid_shipping(self.picking_id)

    def test_validation_street_fails(self):
        self.partner_id.street = "A" * 35
        self.partner_id.street2 = "B" * 35
        with self.assertRaises(UserError):
            self.carrier_id._ensure_valid_shipping(self.picking_id)

    def test_validation_street_succeeds(self):
        self.partner_id.street = "A" * 32
        self.partner_id.street2 = "B" * 32
        self.carrier_id._ensure_valid_shipping(self.picking_id)

    def test_validation_parent_name_fails(self):
        parent_id = self.env["res.partner"].create(
            {
                "name": "A" * 35,
            }
        )

        self.partner_id.parent_id = parent_id
        with self.assertRaises(UserError):
            self.carrier_id._ensure_valid_shipping(self.picking_id)
