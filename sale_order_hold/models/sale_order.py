from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    hold = fields.Boolean(
        default=False,
        copy=False,
        tracking=True,
        readonly=True,
        index=True,
    )

    hold_reason_ids = fields.Many2many(
        "sale.order.hold.reason",
        tracking=True,
    )

    def action_hold(self, reason_id=None, msg=None):
        for record in self.filtered(lambda s: not s.hold):
            record.hold = True
            if reason_id:
                record.hold_reason_ids = reason_id
            if msg:
                record.message_post(body=msg)

    def action_unhold(self, msg=None):
        for record in self.filtered(lambda s: s.hold):
            record.hold = False
            record.hold_reason_ids = False
            if msg:
                record.message_post(body=msg)

    def action_cancel(self):
        if not self._show_cancel_wizard():
            self.action_unhold()

        return super().action_cancel()

    def _action_cancel(self):
        self.action_unhold()
        return super()._action_cancel()
