from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    categ_id = fields.Many2one(
        "project.task.category",
        "Category",
    )

    categ_properties = fields.Properties(
        "Category Properties",
        definition="categ_id.properties_definition",
    )
