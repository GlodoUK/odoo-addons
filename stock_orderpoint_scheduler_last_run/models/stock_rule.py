from odoo import api, fields, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def _run_scheduler_tasks(self, use_new_cursor=False, company_id=False):
        # The cron's lastcall misses Run Scheduler, so stamp it ourselves
        res = super()._run_scheduler_tasks(
            use_new_cursor=use_new_cursor, company_id=company_id
        )
        Company = self.env["res.company"].sudo()
        if company_id:
            companies = Company.browse(company_id)
        else:
            companies = Company.search([])  # pylint: disable=no-search-all
        companies.stock_scheduler_last_run = fields.Datetime.now()
        return res
