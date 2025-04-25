from odoo import fields, models


class EdiBackend(models.Model):
    _inherit = "edi.backend"

    hint_sale_carrier = fields.Many2one(
        "delivery.carrier",
        help="Leave blank for default",
        string="Preferred Sale Carrier",
    )
