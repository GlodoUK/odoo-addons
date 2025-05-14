from odoo import api, fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    brand_id = fields.Many2one(
        "glo.brand",
        "Sale Brand",
    )

    product_tmpl_brand_id = fields.Many2one(
        "glo.brand",
        "Product Brand",
    )

    @api.model
    def _select(self) -> SQL:
        return SQL(
            "%s, move.brand_id, template.brand_id AS product_tmpl_brand_id",
            super()._select(),
        )
