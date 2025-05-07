import json

from odoo import fields, models


class EdiProductTemplate(models.Model):
    _name = "edi.product.template"
    _description = "EDI Product Template"
    _inherit = "edi.binding"
    _inherits = {"product.template": "odoo_id"}

    edi_message_id = fields.Many2one(
        "edi.message",
        index=True,
        auto_join=True,
    )

    odoo_id = fields.Many2one(
        "product.template",
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
        for edi_product_tmpl in self:
            edi_product_tmpl.edi_metadata_string = json.dumps(
                edi_product_tmpl.edi_metadata
            )
