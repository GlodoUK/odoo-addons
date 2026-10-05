from odoo import Command
from odoo.tests.common import TransactionCase


class TestAdvancePaymentForceInvoicedQuantity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Invoiced Elsewhere"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Invoiced Elsewhere Product",
                "default_code": "TEST_SAPFIQ_PRODUCT",
                "invoice_policy": "order",
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {"name": "Invoiced Elsewhere Bank", "type": "bank", "code": "SAPFI"}
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 10,
                            "price_unit": 10,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )
        cls.order.action_confirm()
        cls.order.order_line.force_invoiced_quantity = 4

    def _advance(self, amount):
        self.env["account.voucher.wizard"].with_context(
            active_ids=self.order.ids, active_id=self.order.id
        ).create(
            {
                "journal_id": self.journal.id,
                "payment_type": "inbound",
                "amount_advance": amount,
                "order_id": self.order.id,
            }
        ).make_advance_payment()

    def test_residual_leaves_out_invoiced_elsewhere(self):
        self.assertEqual(self.order.amount_residual, 60)
        self.assertEqual(self.order.advance_payment_status, "not_paid")

    def test_advance_settles_what_is_left(self):
        self._advance(40)
        self.assertEqual(self.order.amount_residual, 20)
        self.assertEqual(self.order.advance_payment_status, "partial")
        self._advance(20)
        self.assertEqual(self.order.amount_residual, 0)
        self.assertEqual(self.order.advance_payment_status, "paid")
