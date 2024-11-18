from odoo import fields, models


class ResBank(models.Model):
    _inherit = "res.bank"

    sort_code = fields.Char(string="Bank Sort Code")
