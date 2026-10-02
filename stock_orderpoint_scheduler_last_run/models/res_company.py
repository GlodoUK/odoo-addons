from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Written under sudo, as only admins may write a company
    stock_scheduler_last_run = fields.Datetime(
        readonly=True,
        groups="stock.group_stock_user",
        help="When the stock scheduler last finished a run.",
    )
