from odoo import fields, models


class EdiBackend(models.Model):
    _inherit = "edi.backend"

    hint_sale_carrier = fields.Many2one(
        "delivery.carrier",
        string="Preferred Sale Carrier",
        hint="Leave blank for default",
    )
