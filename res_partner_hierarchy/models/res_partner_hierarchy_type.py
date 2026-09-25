from odoo import fields, models


class ResPartnerHierarchyType(models.Model):
    _name = "res.partner.hierarchy.type"
    _description = "Partner Hierarchy Type"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _name_uniq = models.Constraint(
        "unique(name)",
        "A hierarchy type with this name already exists.",
    )
