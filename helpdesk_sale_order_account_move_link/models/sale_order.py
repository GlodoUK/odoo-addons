from odoo import models


class SoAmLinkSaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        res = super()._prepare_invoice()

        res.update(
            {
                "helpdesk_ticket_id": self.helpdesk_ticket_id.id,
            }
        )

        return res
