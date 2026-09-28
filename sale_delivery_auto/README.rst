==================
sale_delivery_auto
==================

Picks the delivery method for a sales order, and keeps the shipping cost line
in step with it.

Carrier selection
=================

Every ``delivery.carrier`` in the order's company is considered in sequence
order - the order they are listed in - and the **first one that is available**
for the order is assigned. Availability is core's own test
(``available_carriers``): destination country, state, zip prefix, maximum
weight, maximum volume and product tags.

The selection runs when an order is created, when a field that could change the
answer is written, when order lines are added, changed or removed - whether the
lines are written directly or arrive as one2many commands in a write on the
order, which is how the form saves them - and again on confirmation.

It runs on stored orders only: there is no onchange, so nothing happens while a
form is open and the delivery method appears when the order is saved. The
shipping cost line needs a real ``order_id`` to exist at all, so an onchange
could only ever do half the job, and the "Add shipping" wizard works from a
saved order regardless.

Because the selection is re-run rather than done once, an order always carries
the first carrier that is genuinely available for it - if a change puts the
order over a carrier's weight limit, the next one down the list takes over.

Honouring a manual choice
=========================

A carrier chosen by hand is never replaced.

``delivery_carrier_manual`` is set by one thing: choosing the delivery method
outright, through the "Add shipping" wizard. From that point the order keeps its
carrier, even if that carrier stops being available for it.

Nothing else counts. A bare write to ``carrier_id`` - a script, a connector, an
``import`` - is not a choice, and the selection will answer over it on the next
change. Code that means to pin a carrier says so::

    order.write({"carrier_id": carrier.id, "delivery_carrier_manual": True})

Deleting the shipping cost line does count, though it is not the wizard.
``delivery`` clears ``carrier_id`` when that line goes, so deleting it reads as
"no delivery method, thank you" and is left standing rather than being put
straight back. Our own tidy-up of that line - an order with nothing left to ship
- is not read that way.

Untick **Delivery Method Chosen Manually** on the order to hand the choice back
to the automatic selection.

Shipping cost
=============

The shipping cost line is created and refreshed from
``carrier.rate_shipment()``. This happens for a manually chosen carrier too -
the manual flag protects the choice of carrier, not the price.

Refreshes are driven by an explicit list of trigger fields rather than by every
write.

If the carrier cannot rate the order the failure is logged, ``delivery_message``
is set and ``recompute_delivery_price`` is flagged so the "Update shipping cost"
button appears. The save is never blocked.

Nothing is touched once the order leaves ``draft``/``sent``: after confirmation
the shipping cost is a commercial agreement, not something to quietly re-rate.

Opting out
==========

``skip_delivery_auto=True`` on the context stops both the carrier selection and
the price refresh, for imports, connectors and data migrations::

    order.with_context(skip_delivery_auto=True).write(vals)

There is no per-order opt-out field. For a single order, choosing the delivery
method by hand is the opt-out: that sets *Delivery Method Chosen Manually* and
the selection leaves it alone from then on.

Relationship to the OCA modules
===============================

Replaces ``sale_order_carrier_auto_assign`` and ``delivery_auto_refresh``. Both
are in ``excludes``, along with ``sale_delivery_required``, so Odoo refuses to
install them alongside this module rather than leaving two answers to fight over
an order. The differences that matter:

* ``sale_order_carrier_auto_assign`` only ever considers the partner's
  ``property_delivery_carrier_id``. This module considers every carrier and
  takes the first available one.
* ``delivery_auto_refresh`` re-runs on *every* write to an order or an order
  line. This module runs on a declared set of trigger fields.
* Neither has a notion of a carrier that was chosen deliberately, so a manual
  choice does not survive the next write.
* Both are driven by company-level settings. This module's configuration is in
  code, and opting out is a context key.

``sale_delivery_required`` is excluded for a different reason: it refuses to
confirm an order with no delivery method, and an order with no delivery method
is an answer this module is willing to give - a service-only order, or one whose
shipping cost line was deleted.
