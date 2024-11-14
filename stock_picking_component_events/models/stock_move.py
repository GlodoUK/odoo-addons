from odoo import models


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

    def _action_done(self, cancel_backorder=False):
        fire_picking_event = not self.env.context.get("__no_on_event_picking_out_done")
        _changes, pickings, states = self._on_event_changes_before_dict(
            fire_picking_event
        )

        result = super()._action_done(cancel_backorder=cancel_backorder)

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
