=================
product_fsc_stock
=================

Prints the FSC claim on delivery documents.

Features
========

* Adds an **FSC Certified Products** block to the delivery slip, listing each
  FSC product on the transfer with its claim (e.g. *FSC Mix 70%*) and the
  company's chain-of-custody certificate code.

* Snapshots the product's FSC claim onto the ``stock.move`` when it is created.
  The snapshot depends only on the product, so reclassifying a product later
  does not alter the claim on delivery notes that have already been issued.

Configuration
=============

No configuration is required. The block appears automatically on the delivery
slip for transfers containing FSC-certified products (see ``product_fsc`` for
setting a product's FSC data and the company certificate code).

Depends on ``product_fsc`` and ``stock``.
