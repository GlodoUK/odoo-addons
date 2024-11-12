from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_hold(self, reason_id=None, msg=None):
        res = super().action_hold(reason_id, msg)

        picking_ids = (
            self.sudo()
            .mapped("picking_ids")
            .filtered(lambda p: p.state not in ("done", "cancel"))
        )
        picking_ids.action_hold()

        return res

    def action_unhold(self, msg=None):
        res = super(SaleOrder, self).action_unhold(msg)

        picking_ids = (
            self.sudo()
            .filtered(lambda s: not s.hold)
            .mapped("picking_ids")
            .filtered(lambda p: p.state not in ("done", "cancel"))
        )
        picking_ids.action_unhold()

        return res
