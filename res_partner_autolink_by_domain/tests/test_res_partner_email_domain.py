from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests.common import BaseCase, TransactionCase
from odoo.tools import mute_logger

from odoo.addons.res_partner_autolink_by_domain.tools import normalize_domain

NOT_BARE_DOMAINS = [
    "@acme.test",
    "bob@acme.test",
    "Bob <bob@acme.test>",
    "acme",
    "acme.",
    ".acme.test",
    "acme..test",
    "https://acme.test",
    "acme.test/contact",
    "acme.test:25",
    "*.acme.test",
    "acme test",
    "192.168.0.1",
    "[192.168.0.1]",
    "-acme.test",
    "acme-.test",
    "_acme.test",
    "acme.t",
    "acme.123",
    "a" * 64 + ".test",
]


class TestNormalizeDomain(BaseCase):
    def test_canonical_form(self):
        for given, expected in [
            ("acme.test", "acme.test"),
            ("ACME.TEST", "acme.test"),
            ("  acme.test  ", "acme.test"),
            ("acme.test.", "acme.test"),
            ("sub.acme.test", "sub.acme.test"),
            ("acme-corp.test", "acme-corp.test"),
            ("acme.co.uk", "acme.co.uk"),
            ("a" * 63 + ".test", "a" * 63 + ".test"),
            # Incoming mail gives us punycode, so that is what we store.
            ("äcme.test", "xn--cme-pla.test"),
            ("ÄCME.TEST", "xn--cme-pla.test"),
            ("xn--cme-pla.test", "xn--cme-pla.test"),
        ]:
            with self.subTest(given=given):
                self.assertEqual(normalize_domain(given), expected)

    def test_rejects_anything_but_a_bare_domain(self):
        for given in NOT_BARE_DOMAINS + ["", False, None, 123]:
            with self.subTest(given=given):
                self.assertFalse(normalize_domain(given))


class TestResPartnerEmailDomain(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Acme", "is_company": True}
        )
        cls.other_partner = cls.env["res.partner"].create(
            {"name": "Acme Subsidiary", "is_company": True}
        )
        cls.Domain = cls.env["res.partner.email.domain"]

    def _create(self, name, partner=None):
        return self.Domain.create(
            {"partner_id": (partner or self.partner).id, "name": name}
        )

    def test_name_kept_raw_and_normalized_stored(self):
        domain = self._create("  ACME.TEST. ")
        self.assertEqual(domain.name, "  ACME.TEST. ")
        self.assertEqual(domain.domain_normalized, "acme.test")

    def test_normalized_recomputed_on_write(self):
        domain = self._create("acme.test")
        domain.name = "OTHER.TEST"
        self.assertEqual(domain.domain_normalized, "other.test")

    def test_reject_not_a_bare_domain(self):
        for given in NOT_BARE_DOMAINS:
            with self.subTest(given=given), self.assertRaises(ValidationError):
                self._create(given)

    def test_reject_not_a_bare_domain_on_write(self):
        domain = self._create("acme.test")
        with self.assertRaises(ValidationError):
            domain.name = "bob@acme.test"

    def test_unique_across_partners(self):
        self._create("acme.test")
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            self._create("acme.test", partner=self.other_partner)
            self.env.flush_all()

    def test_unique_ignores_the_form_it_was_typed_in(self):
        """The constraint is on the normalized column, so casing cannot slip a
        duplicate past it."""
        self._create("acme.test")
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            self._create(" ACME.Test. ", partner=self.other_partner)
            self.env.flush_all()

    def test_reject_banned_domain(self):
        self.env["res.partner.email.domain.ban"].create({"name": "shared.test"})
        with self.assertRaises(ValidationError):
            self._create("shared.test")

    def test_reject_seeded_banned_domain(self):
        with self.assertRaises(ValidationError):
            self._create("GMAIL.COM")

    def test_archived_ban_does_not_block(self):
        ban = self.env["res.partner.email.domain.ban"].create({"name": "shared.test"})
        ban.active = False
        self.assertTrue(self._create("shared.test"))

    def test_ban_shares_validation(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner.email.domain.ban"].create({"name": "bob@acme.test"})

    def test_ban_normalized_stored(self):
        ban = self.env["res.partner.email.domain.ban"].create({"name": "SHARED.TEST"})
        self.assertEqual(ban.domain_normalized, "shared.test")
