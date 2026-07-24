from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if order.gatekeeper_hold and order.picking_ids:
                order.picking_ids.action_hold()
                order.picking_ids.write({"gatekeeper_hold": True})
        return res

    def _release_gatekeeper_hold(self):
        self.ensure_one()
        res = super()._release_gatekeeper_hold()
        if self.picking_ids:
            self.picking_ids.write({"gatekeeper_hold": False})
            self.picking_ids.action_unhold()
        return res
