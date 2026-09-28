from odoo import fields, models


class StockLocationFreezeReason(models.Model):
    _name = "stock.location.freeze.reason"
    _description = "Stock Location Freeze Reason"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
