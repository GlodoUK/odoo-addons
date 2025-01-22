from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestChecklists(TransactionCase):
    def setUp(self):
        super().setUp()

        # Set an arbitrary checklist with an arbitrary rule
        # in this example, res.partner records cannot be assigned a salesperson
        # until the checklist is complete
        self.checklist_template = self.env["glo_checklist.template"].create(
            {
                "name": "Test Checklist",
                "res_model_id": self.env.ref("base.model_res_partner").id,
                "domain": [("is_company", "=", False)],
                "block_domain": [("user_id", "!=", False)],
                "block_type": "required",
                "auto_add_view": "all",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Checklist Item",
                            "sequence": 1,
                            "required": True,
                            "prevent_uncomplete": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Another Checklist Item",
                            "sequence": 2,
                            "required": False,
                            "prevent_uncomplete": True,
                        },
                    ),
                ],
            }
        )

        self.partner = self.env["res.partner"].create(
            {"name": "Test Partner", "company_type": "person"}
        )

    def test_checklist_standard(self):
        # Confirm that the checklist is not complete
        with self.assertRaises(ValidationError):
            self.partner.check_checklist_required_completed()
        with self.assertRaises(ValidationError):
            self.partner.check_checklist_fully_completed()

        # Confirm that the partner cannot be assigned a salesperson
        # because the checklist is not complete
        with self.assertRaises(ValidationError):
            self.partner.user_id = self.env.ref("base.user_admin")

        # Complete the required tasks
        self.partner.checklist_item_ids.filtered(lambda x: x.required).completed = True

        self.partner.check_checklist_required_completed()
        with self.assertRaises(ValidationError):
            self.partner.check_checklist_fully_completed()

        # Complete the optional tasks
        self.partner.checklist_item_ids.filtered(
            lambda x: not x.required
        ).completed = True

        self.partner.check_checklist_required_completed()
        self.partner.check_checklist_fully_completed()

        # Confirm that the partner can now be assigned a salesperson
        self.partner.user_id = self.env.ref("base.user_admin")

        self.assertTrue(self.partner.user_id)

    def test_checklist_view(self):
        self.assertTrue(self.partner.get_view().get("arch").find("glo_checklist"))
        self.assertTrue(self.partner.get_view().get("arch").find("Test Checklist"))

    def test_view_options(self):
        self.checklist_template.auto_add_view = "no"
        self.assertEqual(self.partner.get_view().get("arch").find("glo_checklist"), -1)

    def test_blocking_options(self):
        self.checklist_template.block_type = "none"
        self.partner.user_id = self.env.ref("base.user_admin")
        self.assertTrue(self.partner.user_id)

        self.partner.user_id = False
        self.checklist_template.block_type = "required"
        with self.assertRaises(ValidationError):
            self.partner.user_id = self.env.ref("base.user_admin")

        self.partner.checklist_item_ids.filtered(lambda x: x.required).completed = True
        self.partner.user_id = self.env.ref("base.user_admin")
        self.assertTrue(self.partner.user_id)

        self.partner.user_id = False
        self.checklist_template.block_type = "full"

        with self.assertRaises(ValidationError):
            self.partner.user_id = self.env.ref("base.user_admin")

        self.partner.checklist_item_ids.completed = True
        self.partner.user_id = self.env.ref("base.user_admin")
