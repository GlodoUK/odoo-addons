from odoo import models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "product_fsc.line.mixin"]
