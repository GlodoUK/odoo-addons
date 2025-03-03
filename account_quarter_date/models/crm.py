from odoo import api, models


class CRMOpportunity(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "quarter.date.mixin"]

    def _compute_quarter_date_field(self):
        for record in self:
            record.quarter_date_field = "create_date"

    @api.depends("create_date")
    def _compute_fiscal_quarter(self):
        super()._compute_fiscal_quarter()
