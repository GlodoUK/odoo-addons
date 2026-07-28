from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGatekeeperRule(TransactionCase):
    """gatekeeper.rule and gatekeeper.line permission logic.

    The record-matching branches of ``_check_rule`` (record_domain,
    code) need a concrete model that inherits
    ``gatekeeper.mixin``; ``action_gatekeeper`` itself has none, so those
    are covered downstream in ``action_gatekeeper_sale`` (via sale.order).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_a = cls.env["res.users"].create(
            {
                "name": "Gatekeeper User A",
                "login": "gatekeeper_user_a",
                "email": "gatekeeper_user_a@example.com",
            }
        )
        cls.user_b = cls.env["res.users"].create(
            {
                "name": "Gatekeeper User B",
                "login": "gatekeeper_user_b",
                "email": "gatekeeper_user_b@example.com",
            }
        )
        cls.group = cls.env["res.groups"].create({"name": "Gatekeeper Release Group"})

    def _make_rule(self, **values):
        return self.env["gatekeeper.rule"].create(
            {
                "name": "Test Rule",
                "trigger": self.env.ref(
                    "action_gatekeeper.gatekeeper_trigger_create"
                ).id,
                "rule": "always",
                **values,
            }
        )

    def test_check_can_release_direct_user(self):
        rule = self._make_rule(release_users=[(6, 0, [self.user_a.id])])
        self.assertTrue(rule._check_can_release(self.user_a))
        self.assertFalse(rule._check_can_release(self.user_b))

    def test_check_can_release_via_group(self):
        self.group.user_ids = [(4, self.user_a.id)]
        rule = self._make_rule(release_groups=[(6, 0, [self.group.id])])
        self.assertTrue(rule._check_can_release(self.user_a))
        self.assertFalse(rule._check_can_release(self.user_b))

    def test_check_can_release_neither(self):
        rule = self._make_rule()
        self.assertFalse(rule._check_can_release(self.user_a))
        self.assertFalse(rule._check_can_release(self.user_b))

    def test_release_count_required_must_be_positive(self):
        rule = self._make_rule()
        with self.assertRaises(ValidationError):
            rule.release_count_required = 0

    def test_enough_users_can_release_direct_users(self):
        rule = self._make_rule(
            release_users=[(6, 0, [self.user_a.id])],
            release_count_required=2,
        )
        self.assertFalse(rule.enough_users_can_release)
        rule.release_users = [(4, self.user_b.id)]
        self.assertTrue(rule.enough_users_can_release)

    def test_enough_users_can_release_counts_group_members_once(self):
        self.group.user_ids = [(4, self.user_a.id)]
        rule = self._make_rule(
            release_users=[(6, 0, [self.user_a.id])],
            release_groups=[(6, 0, [self.group.id])],
            release_count_required=2,
        )
        # user_a is both a direct release user and a group member, so they
        # only count once towards release_count_required.
        self.assertFalse(rule.enough_users_can_release)
