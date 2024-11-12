from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    hold = fields.Boolean(
        default=False,
        tracking=True,
        copy=True,
        readonly=True,
    )

    def action_cancel(self):
        self.action_unhold()
        return super(StockPicking, self).action_cancel()

    def action_hold(self, **kwargs):
        todo = self.filtered(lambda p: not p.hold and p.state not in ("done", "cancel"))
        if todo:
            todo.write({"hold": True})

        msg = kwargs.get("msg")
        if not msg or not todo:
            return

        for record in todo:
            record.message_post(body=msg)

    def action_unhold(self, **kwargs):
        todo = self.filtered(lambda p: p.hold)
        if todo:
            todo.write({"hold": False})

        msg = kwargs.get("msg")
        if not msg or not todo:
            return

        for record in todo:
            record.message_post(body=msg)

    def button_validate(self):
        for picking in self:
            if picking.hold:
                raise UserError(_("Cannot validate. Picking on hold!"))
        return super(StockPicking, self).button_validate()

    @api.depends("immediate_transfer", "state", "hold")
    def _compute_show_check_availability(self):
        pickings = self.env["stock.picking"]

        for picking in self:
            if picking.hold and any(
                move.state in ("waiting", "confirmed", "partially_available")
                and float_compare(
                    move.product_uom_qty,
                    0,
                    precision_rounding=move.product_uom.rounding,
                )
                for move in picking.move_lines
            ):
                picking.show_check_availability = picking.is_locked
            else:
                pickings |= picking

        return super(StockPicking, pickings)._compute_show_check_availability()

    def _action_done(self):
        self.action_unhold()
        return super(StockPicking, self)._action_done()
