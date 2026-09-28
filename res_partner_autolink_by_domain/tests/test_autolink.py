from odoo.tests import tagged
from odoo.tests.common import TransactionCase


# post_install: these exercise the mail funnel and multi-company behaviour of
# whatever else is installed, which is not all in place during at_install.
@tagged("-at_install", "post_install")
class TestEmailDomainAutolink(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acme = cls.env["res.partner"].create(
            {
                "name": "Acme",
                "is_company": True,
                "email_domain_ids": [(0, 0, {"name": "acme.test"})],
            }
        )
        cls.Partner = cls.env["res.partner"]

    def _find_or_create(self, emails, **kwargs):
        return self.Partner._find_or_create_from_emails(emails, **kwargs)

    def test_new_partner_nested_under_domain_owner(self):
        (partner,) = self._find_or_create(["bob@acme.test"])
        self.assertEqual(partner.parent_id, self.acme)
        self.assertEqual(partner.email, "bob@acme.test")
        self.assertEqual(partner.commercial_partner_id, self.acme)

    def test_name_and_email_forms_still_match(self):
        (partner,) = self._find_or_create(['"Bob" <BOB@ACME.TEST>'])
        self.assertEqual(partner.parent_id, self.acme)
        self.assertEqual(partner.name, "Bob")

    def test_reached_through_the_mail_funnel(self):
        """The gateway goes through mail.thread, not res.partner directly."""
        partner = self.env["mail.thread"]._partner_find_from_emails_single(
            ["bob@acme.test"]
        )
        self.assertEqual(partner.parent_id, self.acme)

    def test_existing_partner_not_reparented(self):
        existing = self.env["res.partner"].create(
            {"name": "Bob", "email": "bob@acme.test"}
        )
        (partner,) = self._find_or_create(["bob@acme.test"])
        self.assertEqual(partner, existing)
        self.assertFalse(partner.parent_id)

    def test_unclaimed_domain_gets_no_parent(self):
        (partner,) = self._find_or_create(["bob@unknown.test"])
        self.assertFalse(partner.parent_id)

    def test_banned_domain_gets_no_parent(self):
        (partner,) = self._find_or_create(["bob@gmail.com"])
        self.assertFalse(partner.parent_id)

    def test_domain_banned_after_assignment_is_inert(self):
        self.env["res.partner.email.domain.ban"].create({"name": "acme.test"})
        (partner,) = self._find_or_create(["bob@acme.test"])
        self.assertFalse(partner.parent_id)

    def test_subdomain_does_not_match(self):
        """Matching is exact: a subdomain has to be listed in its own right."""
        (partner,) = self._find_or_create(["bob@mail.acme.test"])
        self.assertFalse(partner.parent_id)

    def test_explicit_parent_wins(self):
        other = self.env["res.partner"].create({"name": "Other", "is_company": True})
        (partner,) = self._find_or_create(
            ["bob@acme.test"],
            additional_values={"bob@acme.test": {"parent_id": other.id}},
        )
        self.assertEqual(partner.parent_id, other)

    def test_company_mismatch_skipped(self):
        other_company = self.env["res.company"].create({"name": "Other Co"})
        self.acme.company_id = self.env.company
        (partner,) = self._find_or_create(
            ["bob@acme.test"],
            additional_values={"bob@acme.test": {"company_id": other_company.id}},
        )
        self.assertFalse(partner.parent_id)

    def test_company_agnostic_owner_still_matches(self):
        self.assertFalse(self.acme.company_id)
        (partner,) = self._find_or_create(
            ["bob@acme.test"],
            additional_values={"bob@acme.test": {"company_id": self.env.company.id}},
        )
        self.assertEqual(partner.parent_id, self.acme)

    def test_no_create_creates_nothing(self):
        before = self.env["res.partner"].search_count([])
        # A list is returned, holding a falsy value where nothing matched.
        self.assertFalse(any(self._find_or_create(["bob@acme.test"], no_create=True)))
        self.assertEqual(self.env["res.partner"].search_count([]), before)

    def test_batch_of_mixed_emails(self):
        partners = self._find_or_create(
            ["bob@acme.test", "eve@gmail.com", "sue@unknown.test"]
        )
        self.assertEqual(partners[0].parent_id, self.acme)
        self.assertFalse(partners[1].parent_id)
        self.assertFalse(partners[2].parent_id)

    def test_invalid_email_is_untouched(self):
        (partner,) = self._find_or_create(["not-an-email"])
        self.assertFalse(partner.parent_id)
