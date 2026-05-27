from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pdfs_show_product_image = fields.Selection(
        [
            ("product_image_128", "128x128"),
            ("product_image_256", "256x256"),
        ],
        default=False,
    )
