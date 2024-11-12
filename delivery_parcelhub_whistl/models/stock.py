from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    whistl_carrier = fields.Char()
    whistl_tracking_url = fields.Char()
    whistl_shipment_id = fields.Char()


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("whistl", "Whistl")], ondelete={"whistl": "cascade"}
    )
