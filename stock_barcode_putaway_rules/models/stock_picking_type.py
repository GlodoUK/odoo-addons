from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    show_stock_barcode_putaway_rules = fields.Boolean(
        default=False, string="Show 'Apply Putaway Rules' in Barcode"
    )
