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

    def _make_rule(self, action, rule="always", trigger=None, **extra):
        return self.GatekeeperRule.create(
            {
                "name": "Account Move Gatekeeper Rule",
                "target_model": "account.move",
                "trigger": (trigger or self.trigger_post).id,
                "rule": rule,
                "action": action,
                **extra,
            }
        )

    def test_all_block_prevents_post(self):
        self._make_rule(action="block")
        invoice = self._create_invoice(move_type="out_invoice")
        with self.assertRaises(ValidationError):
            invoice.action_post()

    def test_all_hold_sets_hold_and_creates_line_on_post(self):
        rule = self._make_rule(action="hold")
        invoice = self._create_invoice(move_type="out_invoice")
        self.assertFalse(invoice.gatekeeper_hold)
        invoice.action_post()
        self.assertTrue(invoice.gatekeeper_hold)
        self.assertEqual(invoice.gatekeeper_rule_lines.rule_id, rule)

    def test_button_cancel_resets_hold(self):
        self._make_rule(action="hold")
        invoice = self._create_invoice(move_type="out_invoice")
        invoice.action_post()
        self.assertTrue(invoice.gatekeeper_hold)

        invoice.button_cancel()
        self.assertFalse(invoice.gatekeeper_hold)

    def test_button_draft_resets_hold(self):
        self._make_rule(action="hold")
        invoice = self._create_invoice(move_type="out_invoice")
        invoice.action_post()
        self.assertTrue(invoice.gatekeeper_hold)

        invoice.button_draft()
        self.assertFalse(invoice.gatekeeper_hold)

    def test_button_cancel_block_prevents_cancel(self):
        self._make_rule(action="block", trigger=self.trigger_cancel)
        invoice = self._create_invoice(move_type="out_invoice")
        invoice.action_post()
        with self.assertRaises(ValidationError):
            invoice.button_cancel()

    def test_releasing_all_lines_clears_hold(self):
        # Releasing requires acting as an active user: the default
        # TransactionCase user (OdooBot, the technical superuser) is
        # inactive, and released_user_ids is a Many2many to res.users,
        # which silently drops inactive members on read. base.user_admin
        # isn't scoped to the test company here, so reuse the env's own
        # (active, correctly-scoped) user instead.
        releaser = self.env.user
        self._make_rule(action="hold", release_users=[(6, 0, [releaser.id])])
        invoice = self._create_invoice(move_type="out_invoice")
        invoice.action_post()

        line = invoice.gatekeeper_rule_lines
        line.with_user(releaser).action_release()
        self.assertTrue(line.is_released)
        self.assertFalse(invoice.gatekeeper_hold)
