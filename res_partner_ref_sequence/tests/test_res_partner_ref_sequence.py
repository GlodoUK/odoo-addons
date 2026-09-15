from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResPartnerRefSequence(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.default_rule = cls.env.ref("res_partner_ref_sequence.ref_rule_default")
        cls.default_sequence = cls.default_rule.sequence_id

    def _make_company(self, name, **vals):
        return self.env["res.partner"].create(
            {
                "name": f"Test Ref Seq {name}",
                "is_company": True,
                **vals,
            }
        )

    def _make_user(self, login, *groups):
        return (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": f"Test Ref Sequence {login}",
                    "login": f"test_ref_sequence_{login}",
                    "group_ids": [
                        Command.set([self.env.ref(group).id for group in groups])
                    ],
                }
            )
        )

    def _make_sequence(self, name, prefix=None):
        return self.env["ir.sequence"].create(
            {
                "name": f"Test Ref Seq {name}",
                "padding": 7,
                "implementation": "no_gap",
                "prefix": prefix,
            }
        )

    def _make_rule(self, name, domain, sequence=10, prefix=None, **vals):
        return self.env["res_partner_ref_sequence.rule"].create(
            {
                "name": f"Test Ref Seq {name}",
                "domain": domain,
                "sequence": sequence,
                "sequence_id": self._make_sequence(name, prefix).id,
                **vals,
            }
        )

    def test_assign_ref_from_default_rule(self):
        partner = self._make_company("A")
        expected = self.default_sequence.get_next_char(
            self.default_sequence.number_next_actual
        )
        partner.action_generate_ref()
        self.assertEqual(partner.ref, expected)

    def test_assign_ref_is_incrementing(self):
        first = self._make_company("B")
        second = self._make_company("C")
        (first + second).action_generate_ref()
        self.assertTrue(first.ref)
        self.assertTrue(second.ref)
        self.assertNotEqual(first.ref, second.ref)

    def test_assign_ref_keeps_existing(self):
        partner = self._make_company("D", ref="TEST_REF_SEQ_D")
        with self.assertRaises(UserError):
            partner.action_generate_ref()
        self.assertEqual(partner.ref, "TEST_REF_SEQ_D")

    def test_first_matching_rule_wins(self):
        # supplier_rank is non-stored, searchable and computed
        # (partner_manual_rank), so it exercises both matching paths.
        self._make_rule(
            "Suppliers",
            "[('supplier_rank', '>', 0)]",
            prefix="TEST_REF_SEQ_SUP/",
        )
        supplier = self._make_company("E", supplier_rank=1)
        customer = self._make_company("F", customer_rank=1)
        (supplier + customer).action_generate_ref()
        self.assertTrue(supplier.ref.startswith("TEST_REF_SEQ_SUP/"))
        self.assertFalse(customer.ref.startswith("TEST_REF_SEQ_SUP/"))

    def test_lowest_sequence_wins(self):
        first = self._make_rule("First", "[]", sequence=1, prefix="TEST_REF_SEQ_FIRST/")
        self._make_rule("Second", "[]", sequence=2, prefix="TEST_REF_SEQ_SECOND/")
        partner = self._make_company("G")
        self.assertEqual(
            self.env["res_partner_ref_sequence.rule"]._resolve(partner),
            first,
        )
        partner.action_generate_ref()
        self.assertTrue(partner.ref.startswith("TEST_REF_SEQ_FIRST/"))

    def test_archived_rule_is_skipped(self):
        rule = self._make_rule(
            "Archived", "[]", sequence=1, prefix="TEST_REF_SEQ_ARCHIVED/"
        )
        rule.active = False
        partner = self._make_company("H")
        self.assertEqual(
            self.env["res_partner_ref_sequence.rule"]._resolve(partner),
            self.default_rule,
        )
        partner.action_generate_ref()
        self.assertFalse(partner.ref.startswith("TEST_REF_SEQ_ARCHIVED/"))

    def test_no_matching_rule(self):
        self.default_rule.active = False
        partner = self._make_company("I")
        with self.assertRaises(UserError):
            partner.action_generate_ref()

    def test_archived_partner_still_matches(self):
        partner = self._make_company("J", active=False)
        partner.action_generate_ref()
        self.assertTrue(partner.ref)

    def test_invalid_domain_is_refused(self):
        with self.assertRaises(ValidationError):
            self._make_rule("Broken", "[('no_such_field', '=', 1)]")
        with self.assertRaises(ValidationError):
            self._make_rule("Unparseable", "not a domain")
