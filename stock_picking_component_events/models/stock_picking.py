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

        if fire_picking_event:
            for record in self:
                if states.get(record.id) != "assigned" and record.state == "assigned":
                    # generic event
                    self._event("on_picking_assigned").notify(record)

        return ret

    def do_unreserve(self):
        fire_picking_event = not self.env.context.get(
            "__no_on_event_picking_unreserved"
        )

        ret = super(StockPicking, self).do_unreserve()

        if fire_picking_event:
            for picking in self:
                self._event("on_picking_unreserved").notify(picking)

        return ret

    def _action_done(self):
        fire_picking_event = not self.env.context.get("__no_on_event_picking_done")

        # The key in the context avoid the event to be fired in
        # StockMove.action_done(). Allow to handle the partial pickings
        self_context = self.with_context(__no_on_event_picking_out_done=True)
        result = super(StockPicking, self_context)._action_done()

        if fire_picking_event:
            for picking in self:
                method = "partial" if picking.related_backorder_ids else "complete"

                if picking.picking_type_id.code == "outgoing":
                    self._event("on_picking_out_done").notify(picking, method)
                elif (
                    picking.picking_type_id.code == "incoming"
                    and picking.location_dest_id.usage == "customer"
                ):
                    self._event("on_picking_out_dropship_done").notify(picking, method)
                elif (
                    picking.picking_type_id.code == "incoming"
                    and picking.location_dest_id.usage == "internal"
                ):
                    self._event("on_picking_in_done").notify(picking, method)
        return result

    def action_cancel(self):
        fire_picking_event = not self.env.context.get("__no_on_event_picking_cancel")

        # The key in the context avoid the event to be fired in
        # StockMove.action_done(). Allow to handle the partial pickings
        self_context = self.with_context(__no_on_event_picking_cancel=True)
        result = super(StockPicking, self_context).action_cancel()
        if fire_picking_event:
            for picking in self:
                if picking.picking_type_id.code == "outgoing":
                    self._event("on_picking_out_cancel").notify(picking)
                elif (
                    picking.picking_type_id.code == "incoming"
                    and picking.location_dest_id.usage == "customer"
                ):
                    self._event("on_picking_out_dropship_cancel").notify(picking)
                elif (
                    picking.picking_type_id.code == "incoming"
                    and picking.location_dest_id.usage == "internal"
                ):
                    self._event("on_picking_in_cancel").notify(picking)
        return result

    def write(self, vals):
        res = super(StockPicking, self).write(vals)

        if vals and "over_credit" in vals:
            event = "held" if vals.get("over_credit") else "unheld"
            for record in self:
                self._event("on_picking_%s" % (event)).notify(record)

        return res

    def send_collection_to_shipper(self):
        self.ensure_one()
        self.carrier_id.send_collection(self)[0]


class StockMove(models.Model):
    _inherit = "stock.move"

    def _on_event_changes_before_dict(self, fire_picking_event):
        """
        Collects the following before the parent action is carried out;
        1. quantities reserved
        2. pickings and picking states
        """
        moves_qties = {}
        pickings = None
        states = None
        for record in self:
            moves_qties[record.id] = {"previous": record.reserved_availability}

        if fire_picking_event:
            pickings = self.mapped("picking_id")
            states = {p.id: p.state for p in pickings}

        return (moves_qties, pickings, states)

    def _on_event_changes_after_dict(self, changes):
        """
        Using the original values from _on_event_changes_before_dict,
        calculate the changes and throw out on_move_reserved_changed events

        pickings are dealt with manually on a per-method basis as there are
        special cases for the events (i.e. unique names, special checks, etc.)
        """

        fire_event = not self.env.context.get("__no_on_event_move_reserved_changed")

        if not fire_event:
            return changes

        for record in self:
            entry = changes.get(record.id)

            if not entry:
                continue

            change = record.reserved_availability - entry.get("previous", 0)

            if change == 0:
                continue

            entry.update({"current": record.reserved_availability, "change": change})

            record._event("on_move_reserved_changed").notify(record, entry)

        return changes

    def _action_assign(self):
        fire_picking_event = not self.env.context.get("__no_on_event_picking_assigned")

        changes, pickings, states = self._on_event_changes_before_dict(
            fire_picking_event
        )

        result = super(StockMove, self)._action_assign()

        self._on_event_changes_after_dict(changes)

        if not fire_picking_event or not pickings:
            return result

        for picking in pickings:
            if states.get(picking.id) != "assigned" and picking.state == "assigned":
                picking._event("on_picking_assigned").notify(picking)

        return result

    def _action_done(self):
        fire_picking_event = not self.env.context.get("__no_on_event_picking_out_done")
        _changes, pickings, states = self._on_event_changes_before_dict(
            fire_picking_event
        )

        result = super(StockMove, self)._action_done()

        for move in self:
            move._event("on_move_done").notify(move)

        if not fire_picking_event or not pickings:
            return result

        for picking in pickings:
            if states.get(picking.id) != "done" and picking.state == "done":
                # partial pickings are handled in
                # StockPicking.do_transfer()
                if picking.picking_type_id.code == "outgoing":
                    picking._event("on_picking_out_done").notify(picking, "complete")

                if picking.picking_type_id.code == "incoming":
                    picking._event("on_picking_in_done").notify(picking, "complete")

        return result

    def _action_cancel(self):
        fire_picking_event = not self.env.context.get("__no_on_event_picking_cancel")

        changes, pickings, states = self._on_event_changes_before_dict(
            fire_picking_event
        )

        # Super _action_cancel calls _do_unreserve.
        # We need to make sure we dont have a double trigger
        result = super(
            StockMove, self.with_context(__no_on_event_move_reserved_changed=True)
        )._action_cancel()

        self._on_event_changes_after_dict(changes)

        if not fire_picking_event or not pickings:
            return result

        for picking in self:
            # double check the state was moved into cancel from something else
            if states.get(picking.id) != "cancel" and picking.state == "cancel":
                if picking.picking_type_id.code == "outgoing":
                    picking._event("on_picking_out_cancel").notify(picking)

                if picking.picking_type_id.code == "incoming":
                    picking._event("on_picking_in_cancel").notify(picking)

        return result

    def _do_unreserve(self):
        changes, _pickings, _states = self._on_event_changes_before_dict(False)
        result = super(StockMove, self)._do_unreserve()
        self._on_event_changes_after_dict(changes)
        return result
