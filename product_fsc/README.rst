===========
product_fsc
===========

FSC certification data for products, suppliers and your company.

Features
========

* FSC claim on products: *FSC 100%*, *FSC Mix*, *FSC Recycled* or
  *FSC Controlled Wood*, with a percentage for Mix and Recycled.
* FSC product types from FSC-STD-40-004a V2-1, shown as ``[code] name``.
* Supplier certificate, code and expiry on contacts.
* The claim block printed on documents by ``product_fsc_sale`` and
  ``product_fsc_stock``.

Configuration
=============

#. In **Settings > Companies**, set your **FSC Certificate Code**.
#. On a product, tick **FSC Certified** and choose the claim.
#. On a supplier, record their certificate on the **FSC** tab.

Future considerations
=====================

* Claims on lots, falling back to the product.
* Take the delivery claim from the lot when the transfer is validated.
* A ``sale_stock`` bridge to take invoice claims from deliveries, and warn when
  a delivered claim differs from the order.
