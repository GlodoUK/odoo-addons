from random import randint

from odoo import api, fields, models


class GlodoInstanceTag(models.Model):
    _name = "glodo.instance.tag"
    _description = "Instance Tags"
    _order = "name, id"

    @api.model
    def _get_default_color(self):
        return randint(1, 11)

    active = fields.Boolean(
        default=True,
    )

    name = fields.Char(
        required=True,
    )

    color = fields.Integer(
        aggregator=False,
        default=lambda self: self._get_default_color(),
    )
