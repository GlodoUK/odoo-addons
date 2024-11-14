from odoo import api, fields, models


class EdiBackendRouteEvent(models.Model):
    _name = "edi.route.event"
    _description = "EDI Message Route Model Event"

    res_model_id = fields.Many2one(
        "ir.model",
        "Document Model",
        ondelete="cascade",
    )
    res_model = fields.Char(
        "Document Model Name", related="res_model_id.model", readonly=True, store=True
    )
    name = fields.Char(string="Event", required=True)
    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
        compute_sudo=True,
    )

    @api.depends("name", "res_model_id")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.res_model}:{record.name}"

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result
