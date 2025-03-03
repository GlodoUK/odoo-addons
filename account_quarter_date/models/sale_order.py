from odoo import api, models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "quarter.date.mixin"]

    def _compute_quarter_date_field(self):
        for record in self:
            record.quarter_date_field = "date_order"

    @api.depends("date_order")
    def _compute_fiscal_quarter(self):
        super()._compute_fiscal_quarter()
