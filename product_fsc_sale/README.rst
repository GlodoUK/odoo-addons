================
product_fsc_sale
================

Prints the FSC claim on sale orders and customer invoices.

Features
========

* Adds an **FSC Certified Products** block to the sale order and customer
  invoice reports, listing each FSC product with its claim (e.g. *FSC Mix 70%*)
  and the company's chain-of-custody certificate code.

* Snapshots the product's FSC claim onto the ``sale.order.line`` and
  ``account.move.line`` when they are created. The snapshot depends only on the
  product, so reclassifying a product later does not alter documents that have
  already been issued. When an invoice is created from a sale order, the order's
  claim is carried over to the invoice line.

Configuration
=============

No configuration is required. The block appears automatically on the sale order
and invoice for documents containing FSC-certified products (see ``product_fsc``
for setting a product's FSC data and the company certificate code).

Depends on ``product_fsc``, ``sale`` and ``account``.
