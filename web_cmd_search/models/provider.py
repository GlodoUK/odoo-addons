from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WebCmdSearchProvider(models.Model):
    _name = "web.cmd.search.provider"
    _description = "Command Palette Global Search Provider"
    _order = "sequence asc"

    sequence = fields.Integer(default=10)
    model_id = fields.Many2one("ir.model", required=True, ondelete="cascade")
    model_name = fields.Char(string="Model Name", related="model_id.model")
    limit = fields.Integer(default=5)

    @api.constrains("model_id")
    def _model_id_unique(self):
        for record in self:
            if self.search_count([("model_id", "=", record.model_id.id)]) > 1:
                raise ValidationError(
                    _(
                        "Only one provider per model is allowed."
                        " Please update the existing provider."
                    )
                )

    @api.model
    def cmd_search(self, value):
        results = []

        for provider in self.search([]):
            results.extend(
                [
                    {
                        "model": provider.model_id.model,
                        "name": f"{result[1]} - {provider.model_id.name}",
                        "id": result[0],
                    }
                    for result in self.env[provider.model_name].name_search(
                        value, limit=provider.limit
                    )
                ]
            )

        return results
