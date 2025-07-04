from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.carrier_no = cls._create_carrier("no restriction")
        cls.carrier_amount_untaxed = cls._create_carrier(
            "amount untaxed <= 1.0",
            max_sale_order_value_amount=1.0,
            max_sale_order_value_mode="amount_untaxed",
        )
        cls.carrier_amount_total = cls._create_carrier(
            "amount total <= 1.0",
            max_sale_order_value_amount=1.0,
            max_sale_order_value_mode="amount_total",
        )
        cls.partner_id = cls.env["res.partner"].create(
            {
                "name": "Testy McTest Face",
            }
        )
        cls.product_id = cls.env["product.product"].create(
            {
                "name": "Test Shippable Product",
                "type": "consu",
            }
        )
        cls.tax_id = cls.env["account.tax"].create(
            {
                "name": "Carrier Restriction 20%",
                "active": True,
                "amount_type": "percent",
                "amount": 20.0,
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

    @classmethod
    def _create_sale(cls, price_unit, taxes=None):
        tax_id = None
        if taxes:
            tax_id = [Command.set(taxes.ids)]

        return cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_id.id,
                            "price_unit": price_unit,
                            "tax_id": tax_id,
                        },
                    )
                ],
            }
        )

    def test_without_taxes_all_success(self):
        sale_id = self._create_sale(1.0)
        self.assertTrue(self.carrier_no._is_available_for_order(sale_id))
        self.assertTrue(self.carrier_amount_total._is_available_for_order(sale_id))
        self.assertTrue(self.carrier_amount_untaxed._is_available_for_order(sale_id))

    def test_without_taxes_filters(self):
        sale_id = self._create_sale(2.0)
        self.assertTrue(self.carrier_no._is_available_for_order(sale_id))
        self.assertFalse(self.carrier_amount_total._is_available_for_order(sale_id))
        self.assertFalse(self.carrier_amount_untaxed._is_available_for_order(sale_id))

    def test_with_taxes_all_success(self):
        sale_id = self._create_sale(0.0, taxes=self.tax_id)
        self.assertTrue(self.carrier_no._is_available_for_order(sale_id))
        self.assertTrue(self.carrier_amount_total._is_available_for_order(sale_id))
        self.assertTrue(self.carrier_amount_untaxed._is_available_for_order(sale_id))

    def test_with_taxes_filters(self):
        sale_id = self._create_sale(1.0, taxes=self.tax_id)
        self.assertTrue(self.carrier_no._is_available_for_order(sale_id))
        self.assertFalse(self.carrier_amount_total._is_available_for_order(sale_id))
        self.assertTrue(self.carrier_amount_untaxed._is_available_for_order(sale_id))
