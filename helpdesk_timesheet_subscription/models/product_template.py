from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_time_replenisher = fields.Boolean(
        help="Keep on if you want this service to be in partner time balance"
    )
    is_uom_time = fields.Boolean(compute="_compute_is_uom_time", store=True)

    @api.onchange("digits")
    def _compute_is_uom_time(self):
        """Computes boolean for flag that helps show or hide
        is_time_replenisher field"""
        for obj in self:
            if obj.uom_id == self.env.ref("uom.product_uom_hour").id:
                obj.is_uom_time = True
            else:
                obj.is_uom_time = False
