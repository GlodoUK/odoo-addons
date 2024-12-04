from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    lease_schedule_id = fields.Many2one("sale_lease_stock.lease.schedule")
