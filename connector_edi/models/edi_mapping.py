from odoo import api, fields, models


class EdiMapping(models.Model):
    _name = "edi.mapping"
    _description = "EDI Backend Document Mapping"

    backend_id = fields.Many2one(
        "edi.backend",
        required=True,
    )

    res_model_id = fields.Many2one(
        "ir.model",
        "Document Model",
        ondelete="cascade",
        required=True,
    )

    res_id = fields.Integer(
        "Document Model ID",
        required=True,
    )

    ref = fields.Char(
        "Reference",
        required=True,
    )

    comment = fields.Char()

    @api.depends("backend_id", "comment")
    def _compute_display_name(self):
        for mapping in self:
            name = f"{mapping.backend_id.name or repr(mapping.backend_id)}: {mapping.comment or repr(mapping)}"
            mapping.display_name = name

    def record(self):
        self.ensure_one()
        return self.env[self.res_model_id.model].browse(self.res_id)

    # TODO add a nice clickable (widget="reference" field for ease of use)

    def translate_from(self, reference):
        for mapping in self:
            if mapping.ref == reference:
                return self.env[mapping.res_model_id.model].browse(mapping.res_id)

    def translate_to(self, record):
        for mapping in self:
            matches = (
                mapping.res_model_id.model == record._name
                and mapping.res_id == record.id
            )
            if matches:
                return mapping.ref
