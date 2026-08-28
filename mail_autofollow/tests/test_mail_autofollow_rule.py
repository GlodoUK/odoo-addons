from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user


class TestMailAutofollowRule(TransactionCase):
    """res.partner is used as the guinea pig model: it has a chatter and is
    always installed alongside mail.

    Note the plain TransactionCase: the shared BaseCommon disables the whole
    mail machinery (tracking_disable), which is precisely what is under test.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                # keep the noise down without touching auto subscription
                mail_create_nolog=True,
                mail_notrack=True,
                mail_create_nosubscribe=True,
            )
        )
        cls.Rule = cls.env["mail_autofollow.rule"]
        cls.Partner = cls.env["res.partner"]
        cls.partner_model = cls.env.ref("base.model_res_partner")
        cls.follower = cls.Partner.create({"name": "AFR Follower"})
        cls.other_follower = cls.Partner.create({"name": "AFR Other Follower"})
        cls.note_subtype = cls.env.ref("mail.mt_note")
        # res.partner.parent_id (a contact field) and res.partner.user_id (a
        # user field, the Salesperson) are both defined in base, so they are
        # available whatever else is loaded
        cls.field_parent = cls._partner_field("parent_id")
        # create_uid rather than user_id: user_id is tracked, so core's own
        # "subscribe the new responsible" hook would answer for us
        cls.field_user = cls._partner_field("create_uid")

    @classmethod
    def _partner_field(cls, name):
        return cls.env["ir.model.fields"]._get("res.partner", name)

    def setUp(self):
        super().setUp()
        # the rule lookup is ormcached at registry level; a previous test
        # method's rollback would otherwise leave stale ids behind
        self.env.registry.clear_cache()
        self.addCleanup(self.env.registry.clear_cache)

    # -- helpers --------------------------------------------------------

    def _make_rule(self, **vals):
        return self.Rule.create(
            {
                "name": vals.pop("name", "Test rule"),
                "model_id": vals.pop("model_id", self.partner_model.id),
                "partner_ids": vals.pop("partner_ids", [(6, 0, self.follower.ids)]),
                **vals,
            }
        )

    def _followers(self, record):
        # message_partner_ids is computed from the followers table; make sure a
        # previous read in the same test does not answer for a later state
        record.invalidate_recordset(["message_follower_ids", "message_partner_ids"])
        return record.message_partner_ids

    # -- creation -------------------------------------------------------

    def test_subscribed_on_create(self):
        self._make_rule(filter_domain="[('ref', '=', 'AFR-MATCH')]")
        matching = self.Partner.create({"name": "Matching", "ref": "AFR-MATCH"})
        self.assertIn(self.follower, self._followers(matching))

    def test_not_subscribed_when_domain_does_not_match(self):
        self._make_rule(filter_domain="[('ref', '=', 'AFR-MATCH')]")
        other = self.Partner.create({"name": "Other", "ref": "AFR-NOPE"})
        self.assertNotIn(self.follower, self._followers(other))

    def test_empty_domain_matches_every_record(self):
        self._make_rule(filter_domain="[]")
        partner = self.Partner.create({"name": "Anyone"})
        self.assertIn(self.follower, self._followers(partner))

    def test_subscribed_on_create_in_batch(self):
        self._make_rule(filter_domain="[('ref', '=', 'AFR-MATCH')]")
        matching, other = self.Partner.create(
            [
                {"name": "Matching", "ref": "AFR-MATCH"},
                {"name": "Other", "ref": "AFR-NOPE"},
            ]
        )
        self.assertIn(self.follower, self._followers(matching))
        self.assertNotIn(self.follower, self._followers(other))

    def test_inactive_rule_is_ignored(self):
        self._make_rule(filter_domain="[]", active=False)
        partner = self.Partner.create({"name": "Anyone"})
        self.assertNotIn(self.follower, self._followers(partner))

    def test_several_rules_apply(self):
        self._make_rule(name="First", filter_domain="[]")
        self._make_rule(
            name="Second",
            filter_domain="[('ref', '=', 'AFR-MATCH')]",
            partner_ids=[(6, 0, self.other_follower.ids)],
        )
        partner = self.Partner.create({"name": "Matching", "ref": "AFR-MATCH"})
        self.assertIn(self.follower, self._followers(partner))
        self.assertIn(self.other_follower, self._followers(partner))

    # -- update ---------------------------------------------------------

    def test_not_subscribed_on_write_by_default(self):
        self._make_rule(filter_domain="[('ref', '=', 'AFR-MATCH')]")
        partner = self.Partner.create({"name": "Late", "ref": "AFR-NOPE"})
        partner.ref = "AFR-MATCH"
        self.assertNotIn(self.follower, self._followers(partner))

    def test_subscribed_on_write_when_asked(self):
        self._make_rule(
            filter_domain="[('ref', '=', 'AFR-MATCH')]",
            trigger="on_create_or_write",
        )
        partner = self.Partner.create({"name": "Late", "ref": "AFR-NOPE"})
        self.assertNotIn(self.follower, self._followers(partner))
        partner.ref = "AFR-MATCH"
        self.assertIn(self.follower, self._followers(partner))

    def test_write_in_batch_only_subscribes_matching_records(self):
        self._make_rule(
            filter_domain="[('ref', '=', 'AFR-MATCH')]",
            trigger="on_create_or_write",
        )
        matching = self.Partner.create({"name": "Matching", "ref": "AFR-MATCH"})
        other = self.Partner.create({"name": "Other", "ref": "AFR-NOPE"})
        # a single write over both records: the domain is evaluated per record
        (matching + other).write({"comment": "touched"})
        self.assertIn(self.follower, self._followers(matching))
        self.assertNotIn(self.follower, self._followers(other))

    # -- subtypes -------------------------------------------------------

    def test_default_subtypes(self):
        self._make_rule(filter_domain="[]")
        partner = self.Partner.create({"name": "Anyone"})
        follower = self.env["mail.followers"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", partner.id),
                ("partner_id", "=", self.follower.id),
            ]
        )
        expected = self.env["mail.message.subtype"].default_subtypes("res.partner")[0]
        self.assertEqual(follower.subtype_ids, expected)

    def test_explicit_subtypes(self):
        self._make_rule(filter_domain="[]", subtype_ids=[(6, 0, self.note_subtype.ids)])
        partner = self.Partner.create({"name": "Anyone"})
        follower = self.env["mail.followers"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", partner.id),
                ("partner_id", "=", self.follower.id),
            ]
        )
        self.assertEqual(follower.subtype_ids, self.note_subtype)

    def test_existing_follower_is_left_alone(self):
        self._make_rule(filter_domain="[]", subtype_ids=[(6, 0, self.note_subtype.ids)])
        partner = self.Partner.create({"name": "Anyone"})
        follower = self.env["mail.followers"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", partner.id),
                ("partner_id", "=", self.follower.id),
            ]
        )
        # the follower unsubscribed from everything by hand
        follower.subtype_ids = False
        partner.write({"comment": "touched"})
        self.assertFalse(follower.subtype_ids)

    # -- existing records ----------------------------------------------

    def test_apply_to_existing(self):
        untouched = self.Partner.create({"name": "Before", "ref": "AFR-EXIST"})
        self.assertNotIn(self.follower, self._followers(untouched))
        rule = self._make_rule(filter_domain="[('ref', '=', 'AFR-EXIST')]")
        rule.action_apply_to_existing()
        self.assertIn(self.follower, self._followers(untouched))

    def test_apply_to_existing_skips_non_matching(self):
        other = self.Partner.create({"name": "Before", "ref": "AFR-NOPE"})
        rule = self._make_rule(filter_domain="[('ref', '=', 'AFR-EXIST')]")
        rule.action_apply_to_existing()
        self.assertNotIn(self.follower, self._followers(other))

    # -- follower fields ------------------------------------------------

    def test_contact_field_follower(self):
        parent = self.Partner.create({"name": "AFR Parent"})
        self._make_rule(
            filter_domain="[]",
            partner_ids=[(5, 0, 0)],
            follower_field_ids=[(6, 0, self.field_parent.ids)],
        )
        child = self.Partner.create({"name": "Child", "parent_id": parent.id})
        self.assertIn(parent, self._followers(child))

    def test_user_field_follower_subscribes_their_contact(self):
        user = new_test_user(
            self.env,
            login="afr_creator",
            groups="base.group_user,base.group_partner_manager",
        )
        self._make_rule(
            filter_domain="[]",
            partner_ids=[(5, 0, 0)],
            follower_field_ids=[(6, 0, self.field_user.ids)],
        )
        # mail_create_nosubscribe is on, so their contact is only a follower
        # because the rule resolved create_uid to it
        partner = self.Partner.with_user(user).create({"name": "Theirs"})
        self.assertIn(user.partner_id, self._followers(partner.sudo()))

    def test_field_followers_add_to_the_fixed_ones(self):
        parent = self.Partner.create({"name": "AFR Parent"})
        self._make_rule(
            filter_domain="[]",
            follower_field_ids=[(6, 0, self.field_parent.ids)],
        )
        child = self.Partner.create({"name": "Child", "parent_id": parent.id})
        followers = self._followers(child)
        self.assertIn(self.follower, followers)
        self.assertIn(parent, followers)

    def test_field_followers_are_resolved_per_record(self):
        first_parent = self.Partner.create({"name": "AFR Parent 1"})
        second_parent = self.Partner.create({"name": "AFR Parent 2"})
        self._make_rule(
            filter_domain="[]",
            partner_ids=[(5, 0, 0)],
            follower_field_ids=[(6, 0, self.field_parent.ids)],
        )
        first, second, orphan = self.Partner.create(
            [
                {"name": "First", "parent_id": first_parent.id},
                {"name": "Second", "parent_id": second_parent.id},
                {"name": "Orphan"},
            ]
        )
        self.assertEqual(self._followers(first), first_parent)
        self.assertEqual(self._followers(second), second_parent)
        self.assertFalse(self._followers(orphan))

    def test_empty_field_subscribes_nobody(self):
        self._make_rule(
            filter_domain="[]",
            partner_ids=[(5, 0, 0)],
            follower_field_ids=[(6, 0, self.field_parent.ids)],
        )
        orphan = self.Partner.create({"name": "Orphan"})
        self.assertFalse(self._followers(orphan))

    def test_archived_contact_is_not_subscribed(self):
        parent = self.Partner.create({"name": "AFR Parent"})
        parent.action_archive()
        self._make_rule(
            filter_domain="[]",
            partner_ids=[(5, 0, 0)],
            follower_field_ids=[(6, 0, self.field_parent.ids)],
        )
        child = self.Partner.create({"name": "Child", "parent_id": parent.id})
        self.assertFalse(self._followers(child))

    def test_field_followers_on_write(self):
        parent = self.Partner.create({"name": "AFR Parent"})
        self._make_rule(
            filter_domain="[]",
            partner_ids=[(5, 0, 0)],
            follower_field_ids=[(6, 0, self.field_parent.ids)],
            trigger="on_create_or_write",
        )
        child = self.Partner.create({"name": "Child"})
        self.assertFalse(self._followers(child))
        child.parent_id = parent
        self.assertIn(parent, self._followers(child))

    def test_field_followers_apply_to_existing(self):
        parent = self.Partner.create({"name": "AFR Parent"})
        child = self.Partner.create(
            {"name": "Child", "ref": "AFR-EXIST", "parent_id": parent.id}
        )
        self.assertFalse(self._followers(child))
        rule = self._make_rule(
            filter_domain="[('ref', '=', 'AFR-EXIST')]",
            partner_ids=[(5, 0, 0)],
            follower_field_ids=[(6, 0, self.field_parent.ids)],
        )
        rule.action_apply_to_existing()
        self.assertIn(parent, self._followers(child))

    def test_follower_field_of_another_model_is_refused(self):
        field = self.env["ir.model.fields"]._get("res.users", "partner_id")
        with self.assertRaises(ValidationError):
            self._make_rule(filter_domain="[]", follower_field_ids=[(6, 0, field.ids)])

    # -- configuration --------------------------------------------------

    def test_invalid_domain_is_refused(self):
        with self.assertRaises(ValidationError):
            self._make_rule(filter_domain="[('no_such_field', '=', 1)]")

    def test_unparseable_domain_is_refused(self):
        with self.assertRaises(ValidationError):
            self._make_rule(filter_domain="this is not a domain")

    def test_model_without_chatter_is_refused(self):
        with self.assertRaises(ValidationError):
            self._make_rule(model_id=self.env.ref("base.model_res_currency").id)

    def test_subtype_of_another_model_is_refused(self):
        subtype = self.env["mail.message.subtype"].create(
            {"name": "Elsewhere", "res_model": "mail.message"}
        )
        with self.assertRaises(ValidationError):
            self._make_rule(filter_domain="[]", subtype_ids=[(6, 0, subtype.ids)])

    def test_rule_without_follower_does_nothing(self):
        self._make_rule(filter_domain="[]", partner_ids=[(5, 0, 0)])
        partner = self.Partner.create({"name": "Anyone"})
        self.assertNotIn(self.follower, self._followers(partner))

    def test_company_scoped_rule_matches_its_company(self):
        self._make_rule(filter_domain="[]", company_id=self.env.company.id)
        theirs = self.Partner.create(
            {"name": "Theirs", "company_id": self.env.company.id}
        )
        self.assertIn(self.follower, self._followers(theirs))
        shared = self.Partner.create({"name": "Shared"})
        self.assertIn(self.follower, self._followers(shared))

    def test_company_scoped_rule_skips_other_companies(self):
        other = self.env["res.company"].search(
            [("id", "!=", self.env.company.id)], limit=1
        )
        if not other:
            # a second one cannot be created from here: this module loads
            # before account, so account's required columns on res_company are
            # not fields of the registry these tests run against
            self.skipTest("needs a second company")
        self.env.user.company_ids = [(4, other.id)]
        self._make_rule(filter_domain="[]", company_id=other.id)
        ours = self.Partner.create({"name": "Ours", "company_id": self.env.company.id})
        self.assertNotIn(self.follower, self._followers(ours))

    # -- access ---------------------------------------------------------

    def test_plain_user_cannot_configure_rules(self):
        user = new_test_user(self.env, login="afr_user", groups="base.group_user")
        with self.assertRaises(AccessError):
            self.Rule.with_user(user).create(
                {
                    "name": "Sneaky",
                    "model_id": self.partner_model.id,
                    "partner_ids": [(6, 0, self.follower.ids)],
                }
            )

    def _manager(self, login="afr_manager"):
        return new_test_user(
            self.env,
            login=login,
            groups="base.group_user,mail_autofollow.group_mail_autofollow_manager",
        )

    def test_manager_can_read_model_metadata(self):
        """Rendering the rule form reads ir.model / ir.model.fields as the
        acting user, and base.group_user has no rights on either. A manager who
        is not also a settings admin needs them granted by this module.
        """
        rule = self._make_rule(follower_field_ids=[(6, 0, self.field_parent.ids)])
        as_manager = rule.with_user(self._manager("afr_meta"))
        # the m2o and m2many widgets, i.e. display_name on both models
        self.assertTrue(as_manager.model_id.display_name)
        self.assertTrue(as_manager.follower_field_ids.display_name)

    def test_manager_can_browse_model_metadata(self):
        """The dropdowns behind model_id and follower_field_ids search both
        metadata models, filtered by the domains declared on the fields."""
        user = self._manager("afr_browse")
        models = (
            self.env["ir.model"]
            .with_user(user)
            .search([("is_mail_thread", "=", True), ("transient", "=", False)])
        )
        self.assertIn(self.partner_model, models)
        fields = (
            self.env["ir.model.fields"]
            .with_user(user)
            .search(
                [
                    ("model_id", "=", self.partner_model.id),
                    ("relation", "in", ("res.partner", "res.users")),
                ]
            )
        )
        self.assertIn(self.field_parent, fields)

    def test_manager_cannot_edit_model_metadata(self):
        """The grant above is read-only: the rules are configuration, they are
        no licence to redefine the models themselves."""
        user = self._manager("afr_readonly")
        with self.assertRaises(AccessError):
            self.partner_model.with_user(user).write({"name": "Hijacked"})
        with self.assertRaises(AccessError):
            self.field_parent.with_user(user).write({"field_description": "Hijacked"})

    def test_manager_can_configure_rules(self):
        user = self._manager()
        rule = self.Rule.with_user(user).create(
            {
                "name": "Legit",
                "model_id": self.partner_model.id,
                "filter_domain": "[('ref', '=', 'AFR-MATCH')]",
                "partner_ids": [(6, 0, self.follower.ids)],
            }
        )
        self.assertTrue(rule)
        # and the rule applies to records created by anyone
        partner = self.Partner.create({"name": "Matching", "ref": "AFR-MATCH"})
        self.assertIn(self.follower, self._followers(partner))
