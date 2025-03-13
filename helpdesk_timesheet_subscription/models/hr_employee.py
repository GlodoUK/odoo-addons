from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "hr.employee"

    # TODO make this default log appear on tasks timesheets
    glo_default_log_time_id = fields.Many2one(
        comodel_name="product.product",
        domain="[('is_time_replenisher', '=', True),"
        " ('detailed_type', '=', 'service'),"
        " ('sale_ok', '=', True)]",
        help="Product that sets up automatically when employee logs time",
        string="Default Log Time",
    )
