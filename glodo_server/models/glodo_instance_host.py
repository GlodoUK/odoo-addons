from odoo import fields, models


class GlodoInstanceHost(models.Model):
    _name = "glodo.instance.host"
    _description = "Instance Host"
    _order = "name, id"

    active = fields.Boolean(
        default=True,
    )

    name = fields.Char(
        required=True,
    )

    host_properties_definition = fields.PropertiesDefinition(
        "Host Properties",
    )
