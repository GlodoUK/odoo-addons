from odoo import fields, models


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    can_be_consolidated = fields.Boolean(
        help=(
            "Mark this package type as one that can have capacity and can"
            " be consolidated."
        ),
    )
