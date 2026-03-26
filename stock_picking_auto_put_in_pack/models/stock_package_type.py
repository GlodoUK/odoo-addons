from odoo import api, fields, models


class StockPackageTypeCapacity(models.Model):
    _name = "stock.package.type.product.capacity"
    _description = "Stock Packaging Type Capacity by Product"

    product_id = fields.Many2one("product.product", required=True, index=True)
    package_type_id = fields.Many2one("stock.package.type", required=True, index=True)
    quantity = fields.Float(required=True)
    uom_id = fields.Many2one(
        "uom.uom",
        compute="_compute_uom_id",
        store=True,
        readonly=False,
    )

    @api.depends("product_id")
    def _compute_uom_id(self):
        for record in self:
            record.uom_id = record.product_id.uom_id


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    product_capacity_ids = fields.One2many(
        "stock.package.type.product.capacity", "package_type_id"
    )
