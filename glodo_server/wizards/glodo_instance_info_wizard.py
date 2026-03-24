from odoo import fields, models


class GlodoInstanceInfoWizard(models.TransientModel):
    _name = "glodo.instance.info.wizard"
    _description = "Instance Info Display Wizard"

    instance_id = fields.Many2one(
        "glodo.instance",
        readonly=True,
    )

    info_json = fields.Text(
        string="Instance Information",
        readonly=True,
    )
