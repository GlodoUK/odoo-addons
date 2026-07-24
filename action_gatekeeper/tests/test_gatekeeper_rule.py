from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGatekeeperRule(TransactionCase):
    """gatekeeper.rule and gatekeeper.line permission logic.

    The record-matching branches of ``_check_rule`` (record_domain,
    partner_domain, code) need a concrete model that inherits
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
                "trigger": "create",
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
