from odoo import fields, models


class CreditControlClassification(models.Model):
    _name = "credit.control.classification"
    _description = "Credit Control Classification"

    active = fields.Boolean(
        default=True,
    )

    name = fields.Char(
        required=True,
    )
