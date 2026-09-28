from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from odoo.addons.delivery.tests.common import DeliveryCommon
from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestSaleDeliveryRequired(DeliveryCommon, SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.carrier = cls._prepare_carrier(
            product=cls._prepare_carrier_product(name="Test Delivery"),
            name="Test Delivery",
            delivery_type="fixed",
            fixed_price=5.0,
        )

        # Regular salesperson — not a sales manager, so no bypass group
        cls.salesperson = cls.env["res.users"].create(
            {
                "name": "Test Salesperson",
                "login": "test_salesperson_sdr@example.com",
                "group_ids": [
                    (6, 0, [cls.env.ref("sales_team.group_sale_salesman").id])
                ],
            }
        )

    def _make_order(self):
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
            }
        )
        return order

    def _add_delivery(self, order):
        wizard = self.env["choose.delivery.carrier"].create(
            {
                "order_id": order.id,
                "carrier_id": self.carrier.id,
            }
        )
        wizard.button_confirm()

    def test_confirm_without_carrier_raises(self):
        order = self._make_order()
        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_confirm_with_carrier_succeeds(self):
        order = self._make_order()
        self._add_delivery(order)
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_confirm_carrier_id_but_no_delivery_line_raises(self):
        # carrier_id set but delivery line removed — both conditions must hold
        order = self._make_order()
        self._add_delivery(order)
        order.order_line.filtered("is_delivery").unlink()
        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_allow_confirm_without_delivery_bypasses_check(self):
        order = self._make_order()
        order.allow_confirm_without_delivery = True
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_allow_confirm_without_delivery_false_still_requires_delivery(self):
        order = self._make_order()
        order.allow_confirm_without_delivery = False
        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_allow_confirm_without_delivery_with_delivery_still_confirms(self):
        # flag=True + delivery present — should also confirm fine
        order = self._make_order()
        order.allow_confirm_without_delivery = True
        self._add_delivery(order)
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_non_bypass_user_cannot_set_allow_confirm_without_delivery(self):
        order = self._make_order()
        with self.assertRaises(AccessError):
            order.with_user(self.salesperson).write(
                {"allow_confirm_without_delivery": True}
            )
