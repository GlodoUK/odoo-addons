from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    line_sequence = fields.Integer(
        "Line Number",
    )
   
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
       
        for line in res:
            line.order_id._compute_max_line_sequence()
            line.line_sequence = line.order_id.max_line_sequence

        return res
