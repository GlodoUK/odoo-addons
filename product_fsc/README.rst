===========
product_fsc
===========

Records FSC (Forest Stewardship Council) certification data against products and
their suppliers.

Features
========

* An **FSC** section on the product form (enabled by the *FSC Certified* toggle)
  capturing the on-product label claim:

  * ``FSC 100%`` / ``FSC Mix`` / ``FSC Recycled`` classification
  * certified/recycled content percentage (Mix and Recycled only)
  * the FSC trademark licence code printed on the label
  * a computed ``FSC Label`` (e.g. *FSC Mix 70%*)

* Supplier certificate details on the partner form: the certificate document,
  its chain-of-custody code, licence code and expiry date. The certificate
  belongs to the certificate holder, so it is stored once on the partner rather
  than duplicated on every product.

* An *FSC Certified* filter and an *FSC Classification* group-by on the product
  search view.

This module is data-only. To print the FSC claim on business documents, install
``product_fsc_stock`` (delivery notes) and/or ``product_fsc_sale`` (sale orders
and invoices).

Configuration
=============

#. On a product, tick **FSC Certified** and choose the classification. For
   *FSC Mix* / *FSC Recycled*, enter the percentage.
#. On a supplier (contact), open the **FSC** tab to attach the certificate and
   record its code and expiry.
#. In **Settings > Companies**, set your own **FSC Certificate Code** if this
   company issues FSC claims on its own documents.
