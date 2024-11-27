from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def handle_magento_reponse(self, response, backend_id):
        # Here to be overridden if needed
        pass
