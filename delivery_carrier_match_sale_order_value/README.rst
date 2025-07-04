delivery_carrier_match_sale_order_value
=======================================

Allows you to restrict delivery methods/carriers according to a maximum sale order
value.

Use case: Carrier A is cheap, but has a poor reputation when delivering expensive items.

Usage
-----

- Goto Delivery methods
- For each Delivery Method change the max_sale_order_value_mode field from "Any" to
  either option
- Observe delivery method no longer offered either via website, or via add shipping form
  if order value exceeds the configured maximum
