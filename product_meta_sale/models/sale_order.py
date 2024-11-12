from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_invoiceable_lines(self, final=False):
        res = super()._get_invoiceable_lines(final)

        return res.filtered(lambda l: l.meta_visible_to_customer)
