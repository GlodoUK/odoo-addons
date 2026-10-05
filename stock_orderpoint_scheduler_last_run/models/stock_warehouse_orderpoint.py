from odoo import api, models


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    @api.model
    def get_scheduler_last_run(self):
        self.check_access("read")
        return self.env.company.sudo().stock_scheduler_last_run
