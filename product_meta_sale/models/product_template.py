from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    meta_visible_to_customer = fields.Selection(
        [
            ("show", "Detail Shown"),
            ("hide", "Detail Hidden"),
        ],
        string="Detail Customer Visible",
        default="show",
        required=True,
    )
