from odoo import fields, models


class EdiProductTemplate(models.Model):
    _name = "edi.product.template"
    _description = "EDI Product Template"
    _inherit = "edi.binding"
    _inherits = {"product.template": "odoo_id"}

    odoo_id = fields.Many2one(
        "product.template",
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
