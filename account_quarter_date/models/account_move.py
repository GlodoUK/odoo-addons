from odoo import api, fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "quarter.date.mixin"]

    def _compute_quarter_date_field(self):
        for record in self:
            if record.move_type in [
                "out_invoice",
                "in_invoice",
                "out_refund",
                "in_refund",
            ]:
                record.quarter_date_field = "invoice_date"
            else:
                record.quarter_date_field = "date"

    @api.depends("date", "invoice_date")
    def _compute_fiscal_quarter(self):
        super()._compute_fiscal_quarter()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    fiscal_quarter = fields.Char(
        related="move_id.fiscal_quarter",
        store=True,
        string="Fiscal Quarter",
        index=True,
    )
    fiscal_year = fields.Integer(
        related="move_id.fiscal_year",
        store=True,
        string="Fiscal Year (Start Year)",
        index=True,
    )
