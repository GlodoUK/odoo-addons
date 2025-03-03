from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSuitableBankJournals(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.bank_journals = cls.env["account.journal"].search([("type", "=", "bank")])

    def test_ensure_bank_journals(self):
        self.assertTrue(self.bank_journals)

    def test_invalid_move_types(self):
        move_types = [
            "out_invoice",
            "out_refund",
            "in_invoice",
            "in_refund",
            "out_receipt",
            "in_receipt",
        ]

        for move_type in move_types:
            move = self.init_invoice(move_type)

            self.assertTrue(self.bank_journals not in move.suitable_journal_ids)

    def test_valid_type(self):
        move = self.init_invoice("entry")

        self.assertTrue(self.bank_journals not in move.suitable_journal_ids)
