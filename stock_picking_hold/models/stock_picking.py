from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    hold = fields.Boolean(
        readonly=True,
        tracking=True,
    )

    def action_cancel(self):
        self.action_unhold()
        return super().action_cancel()

    def action_hold(self, **kwargs):
        picking_to_hold_ids = self.filtered(
            lambda p: not p.hold and p.state not in ("done", "cancel")
        )

        picking_to_hold_ids.write({"hold": True})

        msg = kwargs.get("msg")
        if msg:
            for picking in picking_to_hold_ids:
                picking.message_post(body=msg)

    def action_unhold(self, **kwargs):
        picking_to_unhold_ids = self.filtered(lambda p: p.hold)

        picking_to_unhold_ids.write({"hold": False})

        msg = kwargs.get("msg")
        if msg:
            for picking in picking_to_unhold_ids:
                picking.message_post(body=msg)

    def button_validate(self):
        held_picking_ids = self.filtered(lambda p: p.hold)
        if held_picking_ids:
            held_names = "\n".join(held_picking_ids.mapped("name"))
            msg = _(
                f"Cannot validate the following pickings because they are on hold:\n{held_names}"  # noqa: E501
            )
            raise UserError(msg)
        return super().button_validate()

    @api.depends(
        "hold",
        "move_ids.product_uom_qty",
        "picking_type_code",
        "state",
    )
    def _compute_show_check_availability(self):
        held_picking_ids = self.filtered(lambda p: p.hold)

        for picking in held_picking_ids:
            if picking.state not in ("confirmed", "waiting", "assigned"):
                picking.show_check_availability = False
                continue

            if all(m.picked for m in picking.move_ids):
                picking.show_check_availability = False
                continue

            show_check_availability = any(
                move.state in ("waiting", "confirmed", "partially_available")
                and float_compare(
                    move.product_uom_qty,
                    0,
                    precision_rounding=move.product_uom.rounding,
                )
                for move in picking.move_ids
            )

            picking.show_check_availability = (
                show_check_availability and picking.is_locked
            )

        return super(
            StockPicking, self - held_picking_ids
        )._compute_show_check_availability()

    def _action_done(self):
        self.action_unhold()
        return super()._action_done()
