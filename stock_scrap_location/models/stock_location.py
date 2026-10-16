from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    scrap_location = fields.Boolean(
        help="If checked, this location is used for scrapping products.",
    )

    _scrap_location_inventory_loss = models.Constraint(
        "CHECK (scrap_location IS NOT TRUE OR usage = 'inventory')",
        "A scrap location must be an Inventory Loss location.",
    )
