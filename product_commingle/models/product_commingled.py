from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductCommingled(models.Model):
    _name = "product.commingled"
    _description = "Product Commingled Line"
    _order = "sequence asc"

    sequence = fields.Integer(default=10)
    parent_product_id = fields.Many2one("product.product", required=True)
    product_id = fields.Many2one("product.product", required=True)

    _sql_constraints = [
        (
            "product_uniq",
            "unique(parent_product_id, product_id)",
            "Product can not be duplicated",
        ),
    ]

    @api.constrains("product_id")
    def _check_uom_category(self):
        for line in self:
            parent_product = line.parent_product_id
            lines = line
            while lines:
                if (
                    parent_product.uom_id.category_id
                    != lines.product_id.uom_id.category_id
                ):
                    raise ValidationError(
                        _(
                            "You cannot mix and match commingled products with"
                            " different UoM categories!\nParent: %(parent)s,"
                            " Child: %(child)s"
                        )
                        % {"parent": parent_product, "child": lines.product_id}
                    )
                lines = lines.mapped("product_id.commingled_ids")

    @api.constrains("product_id")
    def _check_recursion(self):
        for line in self:
            parent_product = line.parent_product_id
            lines = line
            while lines:
                if parent_product in lines.mapped("product_id"):
                    raise ValidationError(
                        _(
                            "You cannot create recursive commingled"
                            " products!\nProduct: %(product)s"
                        )
                        % {"product": parent_product}
                    )
                lines = lines.mapped("product_id.commingled_ids")
