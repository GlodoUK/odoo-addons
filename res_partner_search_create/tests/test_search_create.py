from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestSearchCreate(common.TransactionCase):
    def setUp(self):
        super().setUp()

    def test_search_create(self):
        """
        Test that search_create creates a new partner if one doesn't exist,
        but not if one does exist
        """
        test_name = "Test Customer Ltd (Unit Testing)"
        vals = {
            "name": test_name,
        }

        # Create a Partner, make sure it was created
        test_partner = self.env["res.partner"].search_create(vals)
        self.assertEqual(len(test_partner), 1, "Failed to create new partner!")

        test_search = self.env["res.partner"].search([("name", "=", test_name)])
        self.assertEqual(len(test_search), 1, "Search did not return 1 partner!")

        # Search for created Partner, make sure a new one wasn't created
        self.env["res.partner"].search_create(vals)
        test_search_2 = self.env["res.partner"].search([("name", "=", test_name)])
        self.assertEqual(len(test_search_2), 1, "Duplicate partner was created!")
