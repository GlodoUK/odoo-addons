from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    related_backorder_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="backorder_id",
        string="Related backorders",
    )

    def action_assign(self):
        fire_picking_event = not self.env.context.get("__no_on_event_picking_assigned")

        states = {}

        for record in self:
            states[record.id] = record.state

        ret = super(
            StockPicking, self.with_context(__no_on_event_picking_assigned=True)
        ).action_assign()

        if not fire_picking_event:
            return ret

        for record in self:
            if states.get(record.id) != "assigned" and record.state == "assigned":
                record._event("on_picking_assigned").notify(record)

        return ret

    def do_unreserve(self):
        fire_picking_event = not self.env.context.get(
            "__no_on_event_picking_unreserved"
        )

        ret = super().do_unreserve()

        if not fire_picking_event:
            return ret

        for picking in self:
            picking._event("on_picking_unreserved").notify(picking)

        return ret

    def _action_done(self):
        fire_picking_event = not self.env.context.get("__no_on_event_picking_done")

        # The key in the context avoid the event to be fired in
        # StockMove.action_done(). Allow to handle the partial pickings
        self_context = self.with_context(__no_on_event_picking_out_done=True)
        result = super(StockPicking, self_context)._action_done()

        if not fire_picking_event:
            return result

        for picking in self:
            method = "partial" if picking.related_backorder_ids else "complete"
            event = None

            if picking.picking_type_id.code == "outgoing":
                event = "out"

            elif (
                picking.picking_type_id.code == "incoming"
                and picking.location_dest_id.usage == "customer"
            ):
                event = "out_dropship"

            elif (
                picking.picking_type_id.code == "incoming"
                and picking.location_dest_id.usage == "internal"
            ):
                event = "in"

            if event:
                picking._event(f"on_picking_{event}_done").notify(picking, method)

        return result

    def action_cancel(self):
        fire_picking_event = not self.env.context.get("__no_on_event_picking_cancel")

        # The key in the context avoid the event to be fired in
        # StockMove.action_done(). Allow to handle the partial pickings
        self_context = self.with_context(__no_on_event_picking_cancel=True)
        result = super(StockPicking, self_context).action_cancel()

        if not fire_picking_event:
            return result

        for picking in self:
            event = None

            if picking.picking_type_id.code == "outgoing":
                event = "out"
            elif (
                picking.picking_type_id.code == "incoming"
                and picking.location_dest_id.usage == "customer"
            ):
                event = "out_dropship"
            elif (
                picking.picking_type_id.code == "incoming"
                and picking.location_dest_id.usage == "internal"
            ):
                event = "in"

            if event:
                picking._event(f"on_picking_{event}_cancel").notify(picking)

        return result
