from odoo import fields, models


class EdiMessage(models.Model):
    _inherit = "edi.message"

    edi_sale_order_ids = fields.One2many("edi.sale.order", "edi_message_id")
