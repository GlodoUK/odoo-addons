from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_classification_id = fields.Many2one(
        "product.classification",
        string="Classification",
        index="btree_not_null",
        ondelete="restrict",
        help="Value/volume classification (e.g. from Netstock). Put-away "
        "rules with a classification only apply to matching products.",
    )
