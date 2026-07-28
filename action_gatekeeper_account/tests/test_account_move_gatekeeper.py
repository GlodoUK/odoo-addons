from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMoveGatekeeper(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.GatekeeperRule = cls.env["gatekeeper.rule"]
        cls.trigger_post = cls.env.ref(
            "action_gatekeeper_account.gatekeeper_trigger_action_post"
        )
        cls.trigger_cancel = cls.env.ref(
            "action_gatekeeper_account.gatekeeper_trigger_action_cancel"
        )
        cls.trigger_draft = cls.env.ref(
            "action_gatekeeper_account.gatekeeper_trigger_button_draft"
        )

    def _make_rule(
        self, action, target_move_type, rule="always", trigger=None, **extra
    ):
        return self.GatekeeperRule.create(
            {
                "name": "Account Move Gatekeeper Rule",
                "target_model": "account.move",
                "target_move_type": target_move_type,
                "trigger": (trigger or self.trigger_post).id,
                "rule": rule,
                "action": action,
                **extra,
            }
        )

    def test_all_block_prevents_post(self):
        self._make_rule(action="block", target_move_type="all")
        invoice = self._create_invoice(move_type="out_invoice")
        with self.assertRaises(ValidationError):
            invoice.action_post()

    def test_all_hold_sets_hold_and_creates_line_on_post(self):
        rule = self._make_rule(action="hold", target_move_type="all")
        invoice = self._create_invoice(move_type="out_invoice")
        self.assertFalse(invoice.gatekeeper_hold)
        invoice.action_post()
        self.assertTrue(invoice.gatekeeper_hold)
        self.assertEqual(invoice.gatekeeper_rule_lines.rule_id, rule)

    def test_out_invoice_rule_does_not_match_in_invoice(self):
        self._make_rule(action="block", target_move_type="out_invoice")
        bill = self._create_invoice(move_type="in_invoice")
        bill.action_post()
        self.assertFalse(bill.gatekeeper_hold)

    def test_all_customer_matches_out_invoice_and_out_refund(self):
        self._make_rule(action="hold", target_move_type="all_customer")

        invoice = self._create_invoice(move_type="out_invoice")
        invoice.action_post()
        self.assertTrue(invoice.gatekeeper_hold)

        credit_note = self._create_invoice(move_type="out_refund")
        credit_note.action_post()
        self.assertTrue(credit_note.gatekeeper_hold)

    def test_all_customer_does_not_match_vendor_bill(self):
        self._make_rule(action="block", target_move_type="all_customer")
        bill = self._create_invoice(move_type="in_invoice")
        bill.action_post()
        self.assertFalse(bill.gatekeeper_hold)

    def test_all_vendor_matches_vendor_bill_and_credit_note(self):
        self._make_rule(action="hold", target_move_type="all_vendor")

        bill = self._create_invoice(move_type="in_invoice")
        bill.action_post()
        self.assertTrue(bill.gatekeeper_hold)

        vendor_credit_note = self._create_invoice(move_type="in_refund")
        vendor_credit_note.action_post()
        self.assertTrue(vendor_credit_note.gatekeeper_hold)

    def test_button_cancel_resets_hold(self):
        self._make_rule(action="hold", target_move_type="all")
        invoice = self._create_invoice(move_type="out_invoice")
        invoice.action_post()
        self.assertTrue(invoice.gatekeeper_hold)

        invoice.button_cancel()
        self.assertFalse(invoice.gatekeeper_hold)

    def test_button_draft_resets_hold(self):
        self._make_rule(action="hold", target_move_type="all")
        invoice = self._create_invoice(move_type="out_invoice")
        invoice.action_post()
        self.assertTrue(invoice.gatekeeper_hold)

        invoice.button_draft()
        self.assertFalse(invoice.gatekeeper_hold)

    def test_button_cancel_block_prevents_cancel(self):
        self._make_rule(
            action="block", target_move_type="all", trigger=self.trigger_cancel
        )
        invoice = self._create_invoice(move_type="out_invoice")
        invoice.action_post()
        with self.assertRaises(ValidationError):
            invoice.button_cancel()

    def test_releasing_all_lines_clears_hold(self):
        self._make_rule(action="hold", target_move_type="all")
        invoice = self._create_invoice(move_type="out_invoice")
        invoice.action_post()

        line = invoice.gatekeeper_rule_lines
        line.action_release()
        self.assertTrue(line.is_released)
        self.assertFalse(invoice.gatekeeper_hold)
