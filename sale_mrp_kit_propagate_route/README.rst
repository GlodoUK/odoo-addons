============================
sale_mrp_kit_propagate_route
============================

Ship a kit sold on a sale order from one place, by the **kit's** routes,
rather than each component by its own.

Why
===

Since 13.0, mrp's ``stock.rule.run`` replaces a kit's procurement with one per
component *before* any rule is chosen. Each component then follows its own
product and category routes, and the kit's routes are never read. A kit whose
components carry different routes (e.g. one has "Direct Ship from Anglesey
Road", one has none) ships in several deliveries from several warehouses.

What it does
============

Kit BoMs get **On Sale Components Follow Kit Route** (on by default), which
restores the behaviour of 12.0 and earlier, where the kit's route decided
where its components shipped from. When such a kit is sold on a sale order
and the line has no routes of its own, every component's procurement carries:

#. the kit's product and category routes, or, if it has none,
#. the order warehouse's delivery route,

as if they had been chosen on the line. They outrank the components' own
routes, and follow the chain down (an MTO or Buy step on the way).

Left as core:

* lines with routes chosen on them (or the carrier's routes), which already
  reach every component;
* a component sold on its own;
* kits moved any other way than a sale (the Replenish button, transfers);
* BoMs with the option switched off.

A nested kit follows the kit that was sold.

Known limits
============

* A kit route with no rule to the customer (e.g. only Buy) doesn't send the
  components anywhere; they fall back to their own routes as in core.
