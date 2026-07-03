from odoo_test_helper import FakeModelLoader

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

@tagged("-at_install", "post_install")
class TestEnsureValid(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import TestDeliveryMethod

        cls.loader.update_registry((TestDeliveryMethod,))

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

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

    def test_works_without_method(self):
        # We have no method _fixed_ensure_valid_shipping, ensure that we don't raise any
        # exceptions or break anything
        carrier_id = self._create_carrier(
            "Test Fixed", delivery_type="fixed", validate_before_send_to_shipper=True
        )
        carrier_id._ensure_valid_shipping(self.env["stock.picking"])

    def test_raises(self):
        carrier_id = self._create_carrier(
            "Test Test", delivery_type="test", validate_before_send_to_shipper=True
        )
        with self.assertRaises(UserError):
            carrier_id._ensure_valid_shipping(self.env["stock.picking"])

    def test_does_not_raise_when_disabled(self):
        carrier_id = self._create_carrier(
            "Test Test", delivery_type="test", validate_before_send_to_shipper=False
        )
        carrier_id._ensure_valid_shipping(self.env["stock.picking"])
