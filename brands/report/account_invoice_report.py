from odoo import api, fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    brand_id = fields.Many2one("glo.brand", "Sale Brand", readonly=True)
    product_tmpl_brand_id = fields.Many2one("glo.brand", "Product Brand", readonly=True)

    @api.model
    def _select(self):
        res = super()._select()
        return res + ", move.brand_id, template.brand_id as product_tmpl_brand_id"
