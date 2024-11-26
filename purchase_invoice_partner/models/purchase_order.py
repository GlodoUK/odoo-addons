from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_invoice(self):
        res = super()._prepare_invoice()

        if res.get("partner_id") != self.partner_id.id:
            res.update(
                {
                    "partner_id": self.partner_id.id,
                }
            )

        return res
