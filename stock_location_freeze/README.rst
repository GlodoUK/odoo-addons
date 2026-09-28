=====================
stock_location_freeze
=====================

Freeze a stock location to prevent any further stock movements, reservations, or
putaway operations until the freeze is released.

- Freezing a parent location (e.g. WH/Stock) automatically prevents operations
  on all of its sub-locations.
- Freezing a sub-location does not affect its parent or sibling locations.
- The freeze is enforced at the quant level: both ``_update_available_quantity``
  and ``_update_reserved_quantity`` are blocked for frozen locations.
- The ``_gather`` method filters out quants in frozen locations during
  reservation (via the ``stock_location_freeze_gather`` context key).
- Frozen locations are excluded from putaway rule evaluation.

For developers and integrations that need to bypass the freeze programmatically:

- ``stock_location_freeze_skip``: Set to ``True`` to bypass all freeze checks
  (useful for inventory adjustments or corrections on frozen locations).

Usage
=====

Freezing a Location
-------------------

1. Navigate to a stock location form (Inventory > Configuration > Warehouses >
   Locations, or any location form).
2. Click the **Freeze** button in the header.
3. Select a freeze reason and click **Freeze** to confirm.

If there is reserved stock in the location or its sub-locations, a warning will
be displayed before you confirm.

Once frozen:

- No stock can be moved into or out of the location.
- No reservations can be made against the location.
- Putaway rules will not consider the location as a valid destination.
- All sub-locations are also affected by the freeze.

Unfreezing a Location
---------------------

1. Navigate to the frozen location form.
2. Click the **Unfreeze** button in the header.

The freeze information (who froze it, when, and why) is preserved after
unfreezing for audit purposes. The unfreeze user and date are also recorded.

Freeze Information
------------------

The following fields are displayed on the location form when relevant:

- **Is Frozen?** -- Whether this specific location is frozen.
- **Is Directly or Parent Frozen?** -- Whether this location is frozen
  either directly or because a parent location is frozen.
- **Frozen by Ancestor** -- Whether this location is only frozen because a
  parent location is frozen (not directly frozen itself).
- **Freeze Reason** -- The reason selected when the location was frozen.
- **Frozen By** -- The user who froze the location.
- **Freeze Date** -- When the location was frozen.
- **Unfrozen By** -- The user who last unfroze the location.
- **Unfreeze Date** -- When the location was last unfrozen.

Why use this module vs OCA stock_location_lock
==============================================

The OCA `stock_location_lock` module also provides location locking
functionality, but with an important difference in philosophy:

- **OCA stock_location_lock** requires all stock to be removed from a location
  before it can be locked. This is designed as a permanent or semi-permanent
  state change and is unsuitable when you need to freeze a location in-place.

- **This module (stock_location_freeze)** allows you to freeze a location
  even when stock is still present. This makes it suitable for:

  - **Temporary holds**: Quickly freeze a location for a short period without
    needing to move stock out first.
  - **Cycle counts and audits**: Freeze a location while counting or auditing
    its contents, preventing any movements that would invalidate the count.
  - **Incident response**: Immediately freeze a location when a discrepancy or
    quality issue is detected, preserving the current state for investigation.

In summary, use this module when you need to freeze a location in-situ with
stock still present. Use OCA's module if you want to prevent stock from ever
entering an empty location.
