from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_hold(self, reason_id=None, msg=None):
        res = super().action_hold(reason_id=reason_id, msg=msg)

        picking_ids_to_hold = (
            self.sudo()
            .mapped("picking_ids")
            .filtered(lambda p: p.state not in ("done", "cancel"))
        )

        picking_ids_to_hold.action_hold()

        return res

    def action_unhold(self, msg=None):
        res = super().action_unhold(msg=msg)

        picking_ids_to_unhold = (
            self.sudo()
            .filtered(lambda o: not o.hold)
            .mapped("picking_ids")
            .filtered(lambda p: p.state not in ("done", "cancel"))
        )

        picking_ids_to_unhold.action_unhold()

        return res
