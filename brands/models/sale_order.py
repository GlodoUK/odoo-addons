from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_default_brand(self):
        return self.env["glo.brand"].get_default_record()

    brand_id = fields.Many2one(
        "glo.brand",
        string="Brand",
        help="Select a brand for this sale",
        default=_get_default_brand,
    )

    def _prepare_invoice(self):
        self.ensure_one()
        vals = super()._prepare_invoice()

        if self.brand_id:
            vals["brand_id"] = self.brand_id.id

        return vals
