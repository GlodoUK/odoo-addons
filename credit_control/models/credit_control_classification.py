from odoo import fields, models


class CreditControlClassification(models.Model):
    _name = "credit.control.classification"
    _description = "Hold Policy Classifications"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
