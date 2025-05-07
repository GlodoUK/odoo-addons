import json

from odoo import fields, models


class EdiProductProduct(models.Model):
    _name = "edi.product.product"
    _description = "EDI Product Variant"
    _inherit = "edi.binding"
    _inherits = {"product.product": "odoo_id"}

    edi_message_id = fields.Many2one(
        "edi.message",
        auto_join=True,
        index=True,
    )

    odoo_id = fields.Many2one(
        "product.product",
        string="Base Product",
        required=True,
        ondelete="cascade",
    )

    edi_external_id = fields.Char(
        string="EDI External Reference",
    )

    edi_metadata = fields.Serialized()

    # XXX: Temporary workaround to display serialized field on frontend
    edi_metadata_string = fields.Char(
        compute="_compute_edi_metadata_string",
        string="Metadata",
    )

    def _compute_edi_metadata_string(self):
        for edi_product in self:
            edi_product.edi_metadata_string = json.dumps(edi_product.edi_metadata)
