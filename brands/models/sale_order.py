from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _get_default_brand(self):
        return self.env["glo.brand"].get_default_record()

    brand_id = fields.Many2one(
        "glo.brand",
        default=_get_default_brand,
        help="Select a brand for this sales order",
    )

    def _prepare_invoice(self):
        self.ensure_one()
        vals = super()._prepare_invoice()
        vals["brand_id"] = self.brand_id.id
        return vals
