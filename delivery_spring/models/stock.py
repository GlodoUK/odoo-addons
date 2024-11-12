from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    spring_carrier = fields.Char()
    spring_tracking_url = fields.Char()


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("spring", "Spring")], ondelete={"spring": "cascade"}
    )
