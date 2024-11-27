from odoo import fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "edi.message.mixin"]

    sale_partner_id = fields.Many2one(related="sale_id.partner_id", store=True)
