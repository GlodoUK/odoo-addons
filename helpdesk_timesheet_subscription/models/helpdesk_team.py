from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    glo_product_id = fields.Many2one(
        comodel_name="product.product",
        domain="[('is_time_replenisher', '=', True)]",
        string="Product",
    )
