from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.component.core import Component
from odoo.addons.component.tests.common import ComponentRegistryCase


@tagged("post_install", "-at_install")
class TestAccountMoveComponentEvents(AccountTestInvoicingCommon, ComponentRegistryCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ComponentRegistryCase._setup_registry(cls)

        cls.out_invoice_cancel = []
        cls.out_invoice_open = []
        cls.out_invoice_paid = []

        class AccountMoveListener(Component):
            _name = "test.account.move.listener"
            _inherit = "base.event.listener"
            _apply_on = ["account.move"]

            def on_out_invoice_cancel(self, move_id):
                cls.out_invoice_cancel.append(move_id.id)

            def on_out_invoice_open(self, move_id):
                cls.out_invoice_open.append(move_id.id)

            def on_out_invoice_paid(self, move_id):
                cls.out_invoice_paid.append(move_id.id)

        AccountMoveListener._build_component(cls.comp_registry)

    def test_out_invoice(self):
        self.assertListEqual(
            self.out_invoice_cancel, [], "The tests did not correctly reset!"
        )
        self.assertListEqual(
            self.out_invoice_open, [], "The tests did not correctly reset!"
        )
        self.assertListEqual(
            self.out_invoice_paid, [], "The tests did not correctly reset!"
        )

        move_id = self.init_invoice(
            "out_invoice", products=self.product_a + self.product_b
        )

        move_id.button_cancel()

        self.assertListEqual(
            self.out_invoice_cancel,
            [move_id.id],
            "The event on_out_invoice_cancel should have fired once!",
        )
        self.assertListEqual(
            self.out_invoice_open,
            [],
            "The event on_out_invoice_open shouldn't have fired yet!",
        )
        self.assertListEqual(
            self.out_invoice_paid,
            [],
            "The event on_out_invoice_paid shouldn't have fired yet!",
        )

        move_id.button_draft()

        move_id.action_post()

        self.assertListEqual(
            self.out_invoice_cancel,
            [move_id.id],
            "The event on_out_invoice_cancel should have fired once!",
        )
        self.assertListEqual(
            self.out_invoice_open,
            [move_id.id],
            "The event on_out_invoice_open should have fired once!",
        )
        self.assertListEqual(
            self.out_invoice_paid,
            [],
            "The event on_out_invoice_paid shouldn't have fired yet!",
        )

        # Mark the invoice as paid
        self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=[move_id.id],
            default_amount=move_id.amount_residual,
        ).create({})._create_payments()

        self.assertListEqual(
            self.out_invoice_cancel,
            [move_id.id],
            "The event on_out_invoice_cancel should have fired once!",
        )
        self.assertListEqual(
            self.out_invoice_open,
            [move_id.id],
            "The event on_out_invoice_open should have fired once!",
        )
        self.assertListEqual(
            self.out_invoice_paid,
            [move_id.id],
            "The event on_out_invoice_paid should have fired once!",
        )
