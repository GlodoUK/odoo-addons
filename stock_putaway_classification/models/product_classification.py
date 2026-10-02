from odoo import api, fields, models


class ProductClassification(models.Model):
    _name = "product.classification"
    _description = "Product Classification"
    _order = "sequence, name"
    _rec_names_search = ["name", "code"]

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help="Identifier used by integrations (e.g. Netstock's ProductClassification).",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    @api.depends("name", "code")
    def _compute_display_name(self):
        for classification in self:
            classification.display_name = (
                f"[{classification.code}] {classification.name}"
                if classification.code
                else classification.name
            )

    _name_uniq = models.Constraint(
        "unique (name)",
        "A product classification with this name already exists.",
    )
    _code_uniq = models.Constraint(
        "unique (code)",
        "A product classification with this code already exists.",
    )
