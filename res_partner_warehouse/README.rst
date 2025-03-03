=====================
res_partner_warehouse
=====================

You may want to record the amount of stock available at a partner.

This module is suitable in the following circumstances:

1. You do not own the stock, but need to know how much stock your partner has
   (if you own the stock look at consignment stock first)
2. You do not want to inadvertantly affect your stock valuation through incorrect configuration of a stock.warehouse and stock.location
3. You do not want/need a stock.warehouse and stock.location
4. You do not need a full double entry system
5. You do not want to impact the procurement system within Odoo

res_partner_warehouse provides a simple res.partner.warehouse model, which
represents a single external warehouse. Each warehouse may have multiple
res.partner.warehouse.quant records which describes the products available.

* stock.warehouse is not related to res.partner.warehouse.
* res.partner.warehouse does not support double-entry system.

Q. Why not a field on product.supplierinfo?
A. Because product.supplierinfo can represent price breaks. By adding a field to
this record you need to store the same quantity more than once, which
complicates the question of "how much stock"?

