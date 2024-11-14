from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    cpq_bom_id = fields.Many2one(
        "cpq.dynamic.bom", index=True, context={"active_test": False}
    )
    cpq_bom_line_id = fields.Many2one(
        "cpq.dynamic.bom.line", index=True, context={"active_test": False}
    )
    cpq_description = fields.Char(string="Configurable Product Kit")

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        res = super()._prepare_merge_moves_distinct_fields()
        if self.cpq_bom_id and ("phantom" in self.cpq_bom_id.mapped("type")):
            res.append("cpq_bom_id")
            res.append("cpq_bom_line_id")
        return res

    def _prepare_procurement_values(self):
        res = super()._prepare_procurement_values()
        res["cpq_bom_line_id"] = self.cpq_bom_line_id.id
        res["cpq_bom_id"] = self.cpq_bom_id.id
        res["cpq_description"] = self.cpq_description
        return res
