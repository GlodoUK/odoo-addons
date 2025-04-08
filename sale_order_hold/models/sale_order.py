from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    hold = fields.Boolean(
        copy=False,
        index=True,
        readonly=True,
        tracking=True,
    )

    hold_reason_ids = fields.Many2many(
        "sale.order.hold.reason",
        copy=False,
        tracking=True,
    )

    def action_hold(self, reason_id=None, msg=None):
        for order in self.filtered(lambda s: not s.hold):
            order.hold = True
            if reason_id:
                order.hold_reason_ids = reason_id
            if msg:
                order.message_post(body=msg)

    def action_unhold(self, msg=None):
        for order in self.filtered(lambda o: o.hold):
            order.hold = False
            order.hold_reason_ids = False
            if msg:
                order.message_post(body=msg)

    def _action_cancel(self):
        self.action_unhold()
        return super()._action_cancel()
