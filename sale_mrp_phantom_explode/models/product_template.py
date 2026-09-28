from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Used as a cheap way on the client side so that we can speed up order entry as much
    # as possible, since we must check every single entered product.
    sale_mrp_phantom_explode_ok = fields.Boolean(
        compute="_compute_sale_mrp_phantom_explode_ok", store=True
    )

    @api.depends("bom_ids.sale_explode")
    def _compute_sale_mrp_phantom_explode_ok(self):
        for record in self:
            record.sale_mrp_phantom_explode_ok = any(
                record.bom_ids.mapped("sale_explode")
            )
