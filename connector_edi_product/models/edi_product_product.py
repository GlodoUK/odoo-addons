from odoo import fields, models


class EdiProductProduct(models.Model):
    _name = "edi.product.product"
    _description = "EDI Product Variant"
    _inherit = "edi.binding"
    _inherits = {"product.product": "odoo_id"}

    odoo_id = fields.Many2one(
        "product.product",
        ondelete="cascade",
        required=True,
        string="Base Product",
    )

    edi_message_id = fields.Many2one(
        "edi.message",
        auto_join=True,
        index=True,
    )

    edi_external_id = fields.Char(string="EDI External Reference")
