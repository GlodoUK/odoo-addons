from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


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
            min(len(manual_results), self.provider.limit),
            "'Sales' search returns wrong result count",
        )

        module_results = Provider.cmd_search("Discuss")
        manual_results = self.env["ir.module.module"].name_search("Discuss")
        self.assertEqual(
            len(module_results),
            min(len(manual_results), self.provider.limit),
            "'Discuss' search returns wrong result count",
        )

    def test_one_provider_per_model(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.env["web.cmd.search.provider"].create(
                {"model_id": self.provider.model_id.id}
            )
