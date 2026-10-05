from odoo import fields, models


class StockStorageCategory(models.Model):
    _inherit = "stock.storage.category"

    only_listed_package_types = fields.Boolean(
        help="Packages of a type without a capacity line here don't fit "
        "(core only limits the types listed). Unpackaged stock and packages "
        "without a type are unaffected.",
    )
