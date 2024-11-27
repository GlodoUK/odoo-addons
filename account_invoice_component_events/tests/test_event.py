from odoo import fields
from odoo.tests import tagged

from odoo.addons.component.core import Component
from odoo.addons.component.tests.common import TransactionComponentCase


@tagged("post_install", "-at_install")
class TestEvent(TransactionComponentCase):
    def setUp(self):
        super().setUp()

        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        self.victim_journal = (
            self.env["account.journal"]
            .sudo()
            .search(
                [
                    ("type", "=", "sale"),
                ],
                limit=1,
            )
        )

        if not self.victim_journal:
            self.skipTest("No sale journal found - missing CoA?")

    def test_out_invoice(self):
        out_invoice_did_open = []
        out_invoice_did_cancel = []

        self.assertEqual(len(out_invoice_did_open), 0, "tests did not correctly reset?")
        self.assertEqual(
            len(out_invoice_did_cancel), 0, "tests did not correctly reset?"
        )

        class InvoiceListener(Component):
            _name = "test.account.move.out_invoice.listener"
            _inherit = "base.event.listener"
            _apply_on = ["account.move"]

            def on_out_invoice_open(self, inv):
                out_invoice_did_open.append(inv.id)

            def on_out_invoice_cancel(self, inv):
                out_invoice_did_cancel.append(inv.id)

        InvoiceListener._build_component(self._components_registry)

        out_invoice_move_id = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "journal_id": self.victim_journal.id,
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
                "invoice_date": fields.Date.today(),
            }
        )

        out_invoice_move_id.action_post()
        self.assertListEqual(
            out_invoice_did_open,
            [out_invoice_move_id.id],
            "event should have fired for action_post, for move_type out_invoice",
        )

        out_invoice_move_id.button_cancel()
        self.assertListEqual(
            out_invoice_did_cancel,
            [out_invoice_move_id.id],
            "event should have fired for button_cancel, for move_type out_invoice",
        )

        entry_move_id = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.victim_journal.id,
                "partner_id": self.partner.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.victim_journal.default_account_id.id,
                            "name": "Test line",
                            "price_unit": 00.0,
                        },
                    )
                ],
                "date": fields.Date.today(),
            }
        )

        entry_move_id.action_post()
        self.assertListEqual(
            out_invoice_did_open,
            [out_invoice_move_id.id],
            "event should not have fired for action_post, for move_type entry",
        )

        entry_move_id.button_cancel()
        self.assertListEqual(
            out_invoice_did_cancel,
            [out_invoice_move_id.id],
            "event should not have fired for button_cancel, for move_type entry",
        )
