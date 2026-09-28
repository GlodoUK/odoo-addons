from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    autopilot_sale_binding_ids = fields.One2many(
        "autopilot_sale.order",
        "odoo_id",
        string="Sale EDI Bindings",
    )
