import json

from odoo import fields, models


class EdiProductVariant(models.Model):
    _name = "edi.product.product"
    _inherit = "edi.binding"
    _inherits = {"product.product": "odoo_id"}
    _description = "EDI Product Variant"

    odoo_id = fields.Many2one(
        "product.product", string="Product", required=True, ondelete="cascade"
    )

    edi_message_id = fields.Many2one(
        "edi.message",
        index=True,
        auto_join=True,
        string="Message",
    )

    edi_external_id = fields.Char(string="EDI External Ref")

    edi_metadata = fields.Serialized()
    # XXX: Temporary workaround to display serialized field on frontend
    edi_metadata_string = fields.Char(
        compute="_compute_edi_metadata_string",
        string="Metadata",
    )

    def _compute_edi_metadata_string(self):
        for record in self:
            record.edi_metadata_string = json.dumps(record.edi_metadata)


class EdiProductTemplate(models.Model):
    _name = "edi.product.template"
    _inherit = "edi.binding"
    _inherits = {"product.template": "odoo_id"}
    _description = "EDI Product Template"

    odoo_id = fields.Many2one(
        "product.template", string="Product", required=True, ondelete="cascade"
    )

    edi_message_id = fields.Many2one(
        "edi.message",
        index=True,
        auto_join=True,
    )

    edi_external_id = fields.Char(string="EDI External Ref")

    edi_metadata = fields.Serialized()
    # XXX: Temporary workaround to display serialized field on frontend
    edi_metadata_string = fields.Char(
        compute="_compute_edi_metadata_string",
        string="Metadata",
    )

    def _compute_edi_metadata_string(self):
        for record in self:
            record.edi_metadata_string = json.dumps(record.edi_metadata)
