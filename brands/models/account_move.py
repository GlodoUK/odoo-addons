from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    brand_id = fields.Many2one(
        "glo.brand", string="Brand", help="Select a brand for this Invoice"
    )
