from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    brand_id = fields.Many2one("glo.brand", help="Select a brand for this invoice")
