Sale MOTO Payment
=================

Adds a **Take MOTO Payment** button to confirmed sale orders, allowing staff
to take a Mail Order / Telephone Order (MOTO) card payment on behalf of a
customer without leaving the back-end.

Usage
-----

On any sale order with outstanding amount to invoice, click **Take MOTO
Payment** (visible only when ``invoice_status = 'to invoice'``). A dialog
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
- Invoicing is forced on payment regardless of the ``sale.automatic_invoice``
  system parameter, so orders with a *delivered quantity* invoicing policy are
  invoiced immediately on full payment.
- Draft or sent quotations are confirmed automatically when the payment amount
  meets or exceeds the required confirmation amount.
