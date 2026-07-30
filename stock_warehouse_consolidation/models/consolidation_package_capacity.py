from odoo import api, fields, models


class ConsolidationPackageCapacity(models.Model):
    _name = "consolidation.package.capacity"
    _description = "Package Capacity"
    _order = "product_id, package_type_id"

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        index=True,
        ondelete="cascade",
    )
    package_type_id = fields.Many2one(
        "stock.package.type",
        string="Package Type",
        required=True,
        ondelete="cascade",
        domain="[('can_be_consolidated', '=', True)]",
    )
    max_qty = fields.Float(
        string="Capacity",
        required=True,
        digits="Product Unit of Measure",
        help="Maximum quantity of this product a single package of this type holds.",
    )
    uom_id = fields.Many2one(
        "uom.uom",
        string="Unit",
        related="product_id.uom_id",
    )

    active = fields.Boolean(default=True)

    _product_type_uniq = models.Constraint(
        "unique (product_id, package_type_id)",
        "A capacity is already defined for this product and package type.",
    )
    _max_qty_positive = models.Constraint(
        "check (max_qty > 0)",
        "Package capacity must be greater than zero.",
    )

    @api.model
    def _get_capacity(self, product, package_type):
        if not product or not package_type:
            return 0.0

        capacity = self.search(
            [
                ("product_id", "=", product.id),
                ("package_type_id", "=", package_type.id),
            ],
            limit=1,
        )

        return capacity.max_qty if capacity else 0.0
