stock_picking_state_duration
============================

Adds *Time in State* to transfers: how long a picking has been in its current
state. Empty for draft, done and cancelled transfers.

The duration is computed on read from a stored ``state_date`` stamp, so it is
never stale, and it is sortable in the list view (sorting by duration is
sorting by ``state_date`` in reverse).

On install, ``state_date`` is backfilled from the last tracked ``state``
change in the chatter, falling back to the picking's creation date.
