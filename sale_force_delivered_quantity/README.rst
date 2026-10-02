sale_force_delivered_quantity
=============================

A quantity on the sale order line that counts as delivered without a stock
move: ``force_delivered_quantity``.

It is added, not substituted:

- ``qty_delivered`` is the forced quantity plus whatever the line's moves
  deliver, so the line stays on ``stock_move`` and a real delivery of the rest
  adds on top. A line on ``manual`` is left alone - its delivered quantity is
  whatever was typed.
- ``_get_qty_procurement`` counts it as procured already, so confirming the
  order, and any procurement run after it, only ever orders what is left.

Readonly in the order line list, hidden by default. It is set from code.
