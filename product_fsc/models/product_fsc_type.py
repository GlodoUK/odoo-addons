from odoo import fields, models


class ProductFscType(models.Model):
    _name = "product_fsc.type"
    _description = "FSC Type"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
