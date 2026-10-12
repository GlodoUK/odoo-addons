from odoo.tests import tagged

from odoo.addons.account_payment.tests.common import AccountPaymentCommon
from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestPaymentTransaction(AccountPaymentCommon, SaleCommon):
    def _paid(self, orders):
        tx = self._create_transaction(
            flow="redirect",
            sale_order_ids=orders.ids,
            amount=sum(orders.mapped("amount_total")),
            state="done",
        )
        return tx._create_payment()

    def test_payment_linked_to_its_order(self):
        payment = self._paid(self.sale_order)
        self.assertEqual(payment.sale_id, self.sale_order)
        self.assertEqual(self.sale_order.advance_payment_status, "paid")

    def test_payment_for_several_orders_left_unlinked(self):
        other = self.sale_order.copy()
        payment = self._paid(self.sale_order | other)
        self.assertFalse(payment.sale_id)
