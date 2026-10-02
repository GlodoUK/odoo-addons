from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.stock.models.stock_rule import StockRule


@tagged("post_install", "-at_install")
class TestSchedulerLastRun(TransactionCase):
    def test_a_run_stamps_its_company(self):
        company = self.env.company
        company.stock_scheduler_last_run = False
        with patch.object(StockRule, "_run_scheduler_tasks", return_value=None):
            self.env["stock.rule"]._run_scheduler_tasks(company_id=company.id)
        self.assertTrue(company.stock_scheduler_last_run)
        self.assertEqual(
            self.env["stock.warehouse.orderpoint"].get_scheduler_last_run(),
            company.stock_scheduler_last_run,
        )

    def test_a_failed_run_leaves_the_last_stamp(self):
        company = self.env.company
        company.stock_scheduler_last_run = False
        with (
            patch.object(StockRule, "_run_scheduler_tasks", side_effect=ValueError),
            self.assertRaises(ValueError),
        ):
            self.env["stock.rule"]._run_scheduler_tasks(company_id=company.id)
        self.assertFalse(company.stock_scheduler_last_run)
