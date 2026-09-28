from odoo import fields, models


class ProjectTaskCategory(models.Model):
    _name = "project.task.category"
    _description = "Project Task Category"
    _order = "sequence, name"

    _name_uniq = models.Constraint(
        "unique (name)",
        "A category with the same name already exists.",
    )

    active = fields.Boolean(
        default=True,
    )

    sequence = fields.Integer(
        default=10,
    )

    name = fields.Char(
        required=True,
        translate=True,
    )

    properties_definition = fields.PropertiesDefinition(
        "Properties",
    )
