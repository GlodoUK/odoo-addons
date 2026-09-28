from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    autopilot_sale_binding_ids = fields.One2many(
        "autopilot_sale.picking",
        "odoo_id",
        string="Sale EDI Bindings",
    )
