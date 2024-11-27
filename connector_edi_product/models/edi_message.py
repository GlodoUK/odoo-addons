from odoo import fields, models


class EdiMessage(models.Model):
    _inherit = "edi.message"

    edi_product_tmpl_ids = fields.One2many("edi.product.template", "edi_message_id")
    edi_product_variant_ids = fields.One2many("edi.product.product", "edi_message_id")
