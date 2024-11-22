from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    brand_id = fields.Many2one("glo.brand", "Sale Brand", readonly=True)
    product_tmpl_brand_id = fields.Many2one("glo.brand", "Product Brand", readonly=True)

    def _query(self, with_clause="", fields=False, groupby="", from_clause=""):
        if not fields:
            fields = {}
        if not groupby:
            groupby = ""
        fields.update(
            {
                "brand_id": ", s.brand_id as brand_id",
                "product_tmpl_brand_id": ", t.brand_id as product_tmpl_brand_id",
            }
        )
        groupby += ", s.brand_id, t.brand_id"
        return super()._query(with_clause, fields, groupby, from_clause)
