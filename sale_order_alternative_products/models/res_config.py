from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    sale_alternative_product = fields.Selection(
        [
            ("no_stock", "Alternative Product Without Stock"),
            ("stock", "Alternative Product With Stock"),
        ],
        string="Alternative Product",
        default="stock",
        config_parameter="sale_order_alternative_products.alternative_product",
    )
