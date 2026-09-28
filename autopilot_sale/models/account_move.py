from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    autopilot_sale_binding_ids = fields.One2many(
        "autopilot_sale.invoice",
        "odoo_id",
        string="Sale EDI Bindings",
    )
