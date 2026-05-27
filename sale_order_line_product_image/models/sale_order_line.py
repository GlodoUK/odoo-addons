from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_image_128 = fields.Image(
        related="product_id.image_128",
        store=False,
    )

    product_image_256 = fields.Image(
        related="product_id.image_256",
        store=False,
    )

    product_image_512 = fields.Image(
        related="product_id.image_512",
        store=False,
    )
