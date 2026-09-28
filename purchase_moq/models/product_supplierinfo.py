from odoo import fields, models


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    moq = fields.Float(
        string="Minimum Order Quantity",
        default=0,
    )
