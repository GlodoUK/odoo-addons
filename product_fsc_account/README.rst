===================
product_fsc_account
===================

Prints FSC claims on customer invoices and vendor bills.

Features
========

* FSC claim block on the invoice report (customer invoices and vendor bills).
* Each line keeps the claim it was created with, so reclassifying a product
  doesn't change issued documents. ``product_fsc_sale`` and
  ``product_fsc_purchase`` take the claim from the order instead.
* Optional **FSC Claim** column on invoice and bill lines.
