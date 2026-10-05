sale_advance_payment_force_invoiced_quantity
============================================

Glue between ``sale_advance_payment`` and ``sale_force_invoiced_quantity``.

``sale_advance_payment`` works out what is left to pay on an order as its total,
less advance payments, less what was paid on the order's own invoices. A
quantity marked ``force_invoiced_quantity`` was invoiced outside Odoo, so no
invoice of the order ever covers it and it would sit in the residual for good.
This module takes its value (tax included, at the line's price) out of the
residual, and re-derives the advance payment status from what is left.

What a customer still owes on those outside invoices is on their account, not
the order.
