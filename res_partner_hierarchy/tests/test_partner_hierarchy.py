from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestPartnerHierarchy(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Partner = cls.env["res.partner"]
        cls.grandparent = Partner.create(
            {"name": "RPH Grandparent", "is_company": True}
        )
        cls.rtype = cls.env["res.partner.hierarchy.type"].create(
            {"name": "RPH Subsidiary"}
        )
        cls.parent = Partner.create(
            {
                "name": "RPH Parent",
                "is_company": True,
                "hierarchy_parent_id": cls.grandparent.id,
                "hierarchy_type_id": cls.rtype.id,
            }
        )
        cls.child = Partner.create(
            {
                "name": "RPH Child",
                "is_company": True,
                "hierarchy_parent_id": cls.parent.id,
            }
        )

    def test_complete_name_is_the_whole_branch(self):
        self.assertEqual(self.grandparent.hierarchy_complete_name, "RPH Grandparent")
        self.assertEqual(
            self.parent.hierarchy_complete_name, "RPH Grandparent / RPH Parent"
        )
        self.assertEqual(
            self.child.hierarchy_complete_name,
            "RPH Grandparent / RPH Parent / RPH Child",
        )

    def test_rename_cascades_down_the_branch(self):
        self.grandparent.name = "RPH Holdings"
        self.assertEqual(
            self.child.hierarchy_complete_name, "RPH Holdings / RPH Parent / RPH Child"
        )

    def test_type_is_dropped_with_the_link(self):
        self.assertEqual(self.parent.hierarchy_type_id, self.rtype)
        self.parent.hierarchy_parent_id = False
        self.assertFalse(self.parent.hierarchy_type_id)

    def test_type_in_use_cannot_be_deleted(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.rtype.unlink()

    def test_relink_cascades_down_the_branch(self):
        self.parent.hierarchy_parent_id = False
        self.assertEqual(self.child.hierarchy_complete_name, "RPH Parent / RPH Child")
        self.assertEqual(self.child.hierarchy_root_id, self.parent)

    def test_root_is_the_topmost_ancestor(self):
        self.assertEqual(self.grandparent.hierarchy_root_id, self.grandparent)
        self.assertEqual(self.parent.hierarchy_root_id, self.grandparent)
        self.assertEqual(self.child.hierarchy_root_id, self.grandparent)

    def test_parent_id_is_untouched(self):
        """The hierarchy must not leak into Odoo's own parent tree."""
        self.assertFalse(self.child.parent_id)
        self.assertFalse(self.parent.child_ids)

    def test_cycles_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.grandparent.hierarchy_parent_id = self.child
        with self.assertRaises(ValidationError):
            self.child.hierarchy_parent_id = self.child

    def test_display_name_only_shows_path_under_context(self):
        self.assertEqual(self.child.display_name, "RPH Child")
        self.assertEqual(
            self.child.with_context(hierarchy_show_path=True).display_name,
            "RPH Grandparent / RPH Parent / RPH Child",
        )

    def test_name_search_finds_descendants_under_context(self):
        Partner = self.env["res.partner"]
        found = Partner.with_context(hierarchy_show_path=True).name_search(
            "RPH Grandparent"
        )
        self.assertIn(self.child.id, [rec_id for rec_id, _name in found])
        found = Partner.name_search("RPH Grandparent")
        self.assertNotIn(self.child.id, [rec_id for rec_id, _name in found])
