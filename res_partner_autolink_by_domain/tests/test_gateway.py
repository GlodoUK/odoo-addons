from odoo.orm.model_classes import add_to_registry
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged("-at_install", "post_install")
class TestGateway(TransactionCase):
    """Feed a raw MIME message to the gateway and check what comes out.

    A fake mail.thread model receives the mail so that the test depends on no
    application beyond this module's own dependencies. See ./fake_models.py.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        from .fake_models import AutolinkTestRecord

        add_to_registry(cls.registry, AutolinkTestRecord)
        cls.registry._setup_models__(cls.env.cr, [AutolinkTestRecord._name])
        cls.registry.init_models(
            cls.env.cr, [AutolinkTestRecord._name], {"models_to_check": True}
        )
        cls.addClassCleanup(cls.registry.__delitem__, AutolinkTestRecord._name)
        cls.Record = cls.env[AutolinkTestRecord._name]

        cls.alias_domain = cls.env["mail.alias.domain"].search([], limit=1) or cls.env[
            "mail.alias.domain"
        ].create({"name": "autolink.test"})
        cls.alias = cls.env["mail.alias"].create(
            {
                "alias_name": "autolink-test",
                "alias_domain_id": cls.alias_domain.id,
                "alias_model_id": cls.env["ir.model"]._get_id(AutolinkTestRecord._name),
            }
        )
        cls.alias_email = f"{cls.alias.alias_name}@{cls.alias_domain.name}"

        cls.acme = cls.env["res.partner"].create(
            {
                "name": "Acme",
                "is_company": True,
                "email_domain_ids": [(0, 0, {"name": "acme.test"})],
            }
        )

    def _mime(self, email_from, subject, message_id):
        return (
            "\n".join(
                [
                    "Content-Type: text/plain; charset=utf-8",
                    "MIME-Version: 1.0",
                    "Date: Mon, 3 Aug 2026 10:00:00 +0000",
                    f"From: {email_from}",
                    f"To: {self.alias_email}",
                    f"Subject: {subject}",
                    f"Message-Id: <{message_id}@acme.test>",
                ]
            )
            + "\n\nMy printer is on fire.\n"
        )

    def _process(self, email_from, subject, message_id):
        record_id = self.env["mail.thread"].message_process(
            False, self._mime(email_from, subject, message_id)
        )
        return self.Record.browse(record_id)

    def _partner(self, email):
        return self.env["res.partner"].search([("email_normalized", "=", email)])

    @mute_logger("odoo.addons.mail.models.mail_thread")
    def test_sender_nested_under_domain_owner(self):
        record = self._process('"Bob Smith" <bob@acme.test>', "Printer down", "e2e-1")
        self.assertEqual(record.name, "Printer down")

        bob = self._partner("bob@acme.test")
        self.assertEqual(len(bob), 1, "the sender should have been created once")
        self.assertEqual(bob.name, "Bob Smith")
        self.assertEqual(bob.parent_id, self.acme)
        self.assertEqual(bob.commercial_partner_id, self.acme)
        self.assertEqual(record.partner_id, bob)

    @mute_logger("odoo.addons.mail.models.mail_thread")
    def test_second_sender_same_domain_nests_alongside(self):
        self._process("bob@acme.test", "Printer down", "e2e-2a")
        self._process("sue@acme.test", "Printer down too", "e2e-2b")

        self.assertEqual(
            set(self.acme.child_ids.mapped("email")),
            {"bob@acme.test", "sue@acme.test"},
        )

    @mute_logger("odoo.addons.mail.models.mail_thread")
    def test_banned_sender_domain_gets_no_parent(self):
        self._process("eve@gmail.com", "Printer fine", "e2e-3")

        eve = self._partner("eve@gmail.com")
        self.assertEqual(len(eve), 1, "the sender is still created, just not nested")
        self.assertFalse(eve.parent_id)

    @mute_logger("odoo.addons.mail.models.mail_thread")
    def test_unclaimed_sender_domain_gets_no_parent(self):
        self._process("dan@unknown.test", "Printer ok", "e2e-4")
        self.assertFalse(self._partner("dan@unknown.test").parent_id)

    @mute_logger("odoo.addons.mail.models.mail_thread")
    def test_alias_never_becomes_a_contact(self):
        self._process("bob@acme.test", "Printer down", "e2e-5")
        self.assertFalse(self._partner(self.alias_email))
