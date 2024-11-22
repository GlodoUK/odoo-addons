from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    brand_id = fields.Many2one("glo.brand", "Brand", readonly=True)

    def _query(self, with_clause="", fields=None, groupby="", from_clause=""):
        if not fields:
            fields = {}
        fields["brand_id"] = ", s.brand_id as brand_id"
        groupby += ", s.brand_id"
        return super()._query(with_clause, fields, groupby, from_clause)
