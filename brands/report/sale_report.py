from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    brand_id = fields.Many2one("glo.brand", "Sale Brand", readonly=True)
    product_tmpl_brand_id = fields.Many2one("glo.brand", "Product Brand", readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["brand_id"] = "s.brand_id"
        res["product_tmpl_brand_id"] = "t.brand_id"
        return res

    def _group_by_sale(self):
        groupby = super()._group_by_sale()
        groupby += ", s.brand_id, t.brand_id"
        return groupby
