from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    autopilot_sale_binding_ids = fields.One2many(
        "autopilot_sale.order.line",
        "odoo_id",
        string="Sale EDI Bindings",
    )
