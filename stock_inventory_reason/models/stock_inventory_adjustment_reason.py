from odoo import fields, models


class StockInventoryAdjustmentReason(models.Model):
    _name = "stock.inventory.adjustment.reason"
    _description = "Inventory Adjustment Reason"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        help="Leave empty to make this reason available to all companies.",
    )
