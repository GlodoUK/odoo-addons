from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    plastic_weight = fields.Float(
        digits="Stock Weight",
        help="Weight of plastic per unit in the system weight unit, used to calculate"
        " plastic tax.",
    )
