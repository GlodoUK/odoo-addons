Sale MOTO Payment
=================

Adds a **MOTO Payment & Confirm** button to quotations, allowing staff to take
a Mail Order / Telephone Order (MOTO) card payment on behalf of a customer
without leaving the back-end.

Usage
-----

On a draft or sent quotation, click **MOTO Payment & Confirm**. A dialog
opens with an **Open Payment Window** button.

Clicking it launches a native browser popup containing the standard Odoo
payment form. Once the customer's card details are submitted and the
provider confirms the transaction, the popup closes automatically and the sale
order view reloads.

Behaviour
---------

- The payment popup is sized to match Odoo's default modal width and is
  centred over the current browser window, including on multi-monitor setups.
- If the popup is closed before payment is completed the dialog remains open
  and offers a **Reopen** link.
- Transactions are flagged ``is_moto = True`` on ``payment.transaction``.
- Customer-facing emails (order confirmation, payment succeeded notification)
  are suppressed for MOTO transactions.
- No invoice is raised on payment: the order is invoiced the usual way (or on
  payment if ``sale.automatic_invoice`` is on, as for any online payment).
  See *Prepayments* below.
- Draft or sent quotations are confirmed automatically when the payment amount
  meets or exceeds the required confirmation amount.

Prepayments
-----------

On its own, a MOTO payment is booked to the customer's account but isn't tied
to the order it paid for. Until the order is invoiced, it looks like the
customer is in credit, and nothing matches the payment to the invoice when it
arrives.

Install these alongside this module to fix that:

- ``sale_advance_payment`` (OCA ``sale-workflow``): records payments against a
  sale order, shows the order's advance payment status and remaining balance,
  and reconciles those payments against the order's invoice when it is posted.
- ``sale_advance_payment_transaction``: links the payment from a settled
  transaction to its sale order, so ``sale_advance_payment`` picks it up. It
  installs automatically with ``sale_advance_payment``, and covers every
  online payment for a single order (portal, website), not only MOTO ones.

This module doesn't depend on either, so it works without them. Payments then
stay on account and are matched to invoices by hand.
