=====================================
backport_stock_removal_least_packages
=====================================

.. WARNING::
   USE AT YOUR OWN RISK
   This module is a best effort BACKPORT of functionality from a later Odoo version
   Test thoroughly in a non-production environment before deploying.

Backports the **Least Packages** stock removal strategy from **Odoo 17.0**
version to **Odoo 15.0**.

When this removal strategy is assigned to a product or location, Odoo will
try to fulfil reservations using the **fewest number of packages** possible,
rather than consuming packages one-by-one. This reduces package fragmentation
and helps keep warehouse operations clean.

Usage
=====

Setting the Removal Strategy
-----------------------------

1. Navigate to **Inventory > Configuration > Locations** (or open a product's
   storage configuration).
2. Set the **Removal Strategy** field to **Least Packages**.

Once set, any stock reservation for products in that location will use the
least-packages algorithm when calculating which quants to reserve.

Limitations
===========

- This is a best-effort backport. Expect slight behavioural differences with 17.0+.
- The A* search has a memory guard; very large package sets may fall back to
  default behaviour.
- The removal strategy order returned by ``_get_removal_strategy_order`` is a
  placeholder (``in_date ASC``) and is not fully respected during reservation
  — the A* result determines actual quant selection.
