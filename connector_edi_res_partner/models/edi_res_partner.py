import json

from odoo import fields, models


class EdiResPartner(models.Model):
    _name = "edi.res.partner"
    _description = "EDI Contact Binding"
    _inherit = "edi.binding"
    _inherits = {"res.partner": "odoo_id"}

    odoo_id = fields.Many2one("res.partner", required=True, ondelete="cascade")

    edi_message_id = fields.Many2one(
        "edi.message",
        index=True,
        required=False,
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
