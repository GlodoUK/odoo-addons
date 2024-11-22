from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.partner_id.property_purchase_journal_id:
            res.update(
                {
                    "journal_id": self.partner_id.property_purchase_journal_id.id,
                }
            )
        return res
