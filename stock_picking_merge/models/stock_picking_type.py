from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    allow_merge = fields.Boolean(
        default=False,
        help="If enabled, pickings of this type can be merged together via the"
        " Merge Pickings action.",
    )
