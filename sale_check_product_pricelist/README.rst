============================
sale_check_product_pricelist
============================

Lets a pricelist declare *which products may be sold against it*, rather than
only what they cost.

Odoo's default is permissive: if no pricelist rule matches a product, the sale
price is used as a fallback, so anything in the catalogue is sellable on any
pricelist. For customers working from an agreed price book (contracts, framework
agreements) that is wrong — an off-book product should not quietly go out at
MSRP.

Configuration
=============

On the pricelist form, **Sellable Products**:

* *Odoo default - fallback to MSRP* — unchanged behaviour.
* *Only those on Pricelist* — confirming an order is blocked unless every line
  matches a rule on the pricelist. A rule computed from another pricelist (a
  discount or formula based on "Other Pricelist") only passes the product on:
  when that pricelist is also *Only those on Pricelist*, the product has to be
  on it as well, and so on down the chain.

The check runs on confirmation via ``_confirmation_error_message``, so drafts and
quotations can still be built up freely; the error names the offending products.
