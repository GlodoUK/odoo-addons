from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSearchResults(TransactionCase):
    def setUp(self):
        super().setUp()
        module_model = self.env["ir.model"].search([("name", "=", "Module")])
        self.provider = self.env["web.cmd.search.provider"].search(
            [("model_id", "=", module_model.id)], limit=1
        )
        if not self.provider:
            self.provider = self.env["web.cmd.search.provider"].create(
                {
                    "model_id": module_model.id,
                    "limit": 8,
                }
            )

    def test_search_results(self):
        Provider = self.env["web.cmd.search.provider"]

        module_results = Provider.cmd_search("Sales")
        manual_results = self.env["ir.module.module"].name_search("Sales")
        self.assertEqual(
            len(module_results),
            self.provider.limit
            if len(manual_results) > self.provider.limit
            else len(manual_results),
            "'Sales' search returns wrong result count",
        )

        module_results = Provider.cmd_search("Discuss")
        manual_results = self.env["ir.module.module"].name_search("Discuss")
        self.assertEqual(
            len(module_results),
            self.provider.limit
            if len(manual_results) > self.provider.limit
            else len(manual_results),
            "'Discuss' search returns wrong result count",
        )
