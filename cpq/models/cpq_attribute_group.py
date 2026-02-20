from odoo import fields, models


class CpqAttributeGroup(models.Model):
    _name = "cpq.attribute.group"
    _description = "CPQ Attribute Group"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
