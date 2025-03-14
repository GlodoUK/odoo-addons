from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update(
            {
                "helpdesk_ticket_ids": [(6, 0, self.helpdesk_tickets_ids.ids)],
            }
        )

        return res
