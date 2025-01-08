from odoo_test_helper import FakeModelLoader

from odoo import _
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMailForwarding(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Load our test model
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models.test_model import FakeTestModel

        cls.loader.update_registry((FakeTestModel,))

        cls.model_fake_test = cls.env["ir.model"].search(
            [("model", "=", "fake.test.model")]
        )

        cls.partner_forward_target = cls.env["res.partner"].create(
            {
                "name": "Forwarding Target",
            }
        )

        cls.partner_forwarder = cls.env["res.partner"].create(
            {
                "name": "Partner to Forward From",
                "forwarding_enabled": False,
            }
        )

        cls.record_fake_test = cls.env["fake.test.model"].create(
            {"partner_id": cls.partner_forwarder.id}
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        return super().tearDownClass()

    def test_disabled_forwarding(self):
        self.assertEqual(
            self.partner_forwarder,
            self.partner_forwarder._forwarding_to_partner("fake.test.model"),
            "When forwarding_enabled = False, it should not attempt to forward",
        )

    def test_enabled_empty_ruleset(self):
        self.partner_forwarder.forwarding_enabled = True

        self.assertEqual(
            self.partner_forwarder,
            self.partner_forwarder._forwarding_to_partner("fake.test.model"),
            "When not rules are set, partner should not forward!",
        )

    def test_ruleset_all(self):
        self.partner_forwarder.write(
            {
                "forwarding_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "mode": "all",
                            "forwarding_to_partner_id": self.partner_forward_target.id,
                        },
                    )
                ],
                "forwarding_enabled": True,
            }
        )

        self.assertEqual(
            self.partner_forward_target,
            self.partner_forwarder._forwarding_to_partner("fake.test.model"),
        )

    def test_ruleset_includes(self):
        self.partner_forwarder.write(
            {
                "forwarding_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "mode": "include",
                            "model_id": self.model_fake_test.id,
                            "forwarding_to_partner_id": self.partner_forward_target.id,
                        },
                    )
                ],
                "forwarding_enabled": True,
            }
        )

        self.assertEqual(
            self.partner_forwarder,
            self.partner_forwarder._forwarding_to_partner("res.partner"),
        )

        self.assertEqual(
            self.partner_forward_target,
            self.partner_forwarder._forwarding_to_partner("fake.test.model"),
        )

    def test_ruleset_excludes(self):
        self.partner_forwarder.write(
            {
                "forwarding_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "mode": "exclude",
                            "model_id": self.model_fake_test.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "mode": "all",
                            "forwarding_to_partner_id": self.partner_forward_target.id,
                        },
                    ),
                ],
                "forwarding_enabled": True,
            }
        )

        self.assertEqual(
            self.partner_forwarder,
            self.partner_forwarder._forwarding_to_partner("fake.test.model"),
        )

        self.assertEqual(
            self.partner_forward_target,
            self.partner_forwarder._forwarding_to_partner("res.partner"),
        )

    def test_message_post_all(self):
        self.partner_forwarder.write(
            {
                "forwarding_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "mode": "all",
                            "forwarding_to_partner_id": self.partner_forward_target.id,
                        },
                    )
                ],
                "forwarding_enabled": True,
            }
        )

        self.record_fake_test.message_post(
            body=_("Test"),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            partner_ids=[self.partner_forwarder.id],
        )

        self.assertEqual(
            self.record_fake_test.message_ids.notified_partner_ids,
            self.partner_forward_target,
        )

        self.assertEqual(
            len(self.record_fake_test.message_ids.forwarded_partner_history_ids), 1
        )

    def test_message_post_exclude(self):
        self.partner_forwarder.write(
            {
                "forwarding_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "mode": "exclude",
                            "model_id": self.model_fake_test.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "mode": "all",
                            "forwarding_to_partner_id": self.partner_forward_target.id,
                        },
                    ),
                ],
                "forwarding_enabled": True,
            }
        )

        self.record_fake_test.message_post(
            body=_("Test"),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            partner_ids=[self.partner_forwarder.id],
        )

        self.assertEqual(
            self.record_fake_test.message_ids.notified_partner_ids,
            self.partner_forwarder,
        )

        self.assertEqual(
            len(self.record_fake_test.message_ids.forwarded_partner_history_ids), 0
        )

    def test_message_post_include(self):
        self.partner_forwarder.write(
            {
                "forwarding_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "mode": "include",
                            "model_id": self.model_fake_test.id,
                            "forwarding_to_partner_id": self.partner_forward_target.id,
                        },
                    ),
                ],
                "forwarding_enabled": True,
            }
        )

        self.record_fake_test.message_post(
            body=_("Test"),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            partner_ids=[self.partner_forwarder.id],
        )

        self.assertEqual(
            self.record_fake_test.message_ids.notified_partner_ids,
            self.partner_forward_target,
        )

        self.assertEqual(
            len(self.record_fake_test.message_ids.forwarded_partner_history_ids), 1
        )

        self.assertEqual(
            self.record_fake_test.message_ids.forwarded_partner_history_ids.replaced_partner_id,
            self.partner_forwarder,
        )

        self.assertEqual(
            self.record_fake_test.message_ids.forwarded_partner_history_ids.partner_id,
            self.partner_forward_target,
        )
