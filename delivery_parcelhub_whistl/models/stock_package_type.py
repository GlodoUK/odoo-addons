from odoo import fields, models


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("whistl", "Whistl")], ondelete={"whistl": "cascade"}
    )
