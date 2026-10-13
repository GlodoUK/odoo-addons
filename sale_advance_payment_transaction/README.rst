sale_advance_payment_transaction
================================

Glue between ``sale_advance_payment`` and online payments.

A payment taken through a payment provider (portal, website or MOTO) books an
``account.payment`` but leaves it unattached to the order it paid for, so
nothing reconciles it when the order is invoiced. This module sets its
``sale_id`` when the transaction is for a single order, the same as payments
from ``sale_advance_payment``'s own wizard. The order then shows as paid in
advance, and its invoice reconciles against the payment when posted.

Transactions covering several orders are left unlinked, as there is no way to
tell which order each part of the payment belongs to.
