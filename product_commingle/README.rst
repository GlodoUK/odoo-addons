=================
product_commingle
=================

Provides primitives for the commingling of products.

:warning: By itself this module does nothing. `product_commingle_mrp` and `product_commingle_stock` are the ultimate workhorses.

Supports the scenario where you have a product which is a composite of other products
(but not a kit).

This module is built to supersede `mrp_phantom_equiv` for the following reasons:

1. Allows for installations without `mrp` by making it optional through `product_commingle_mrp`.
2. Under 13.0+ changes with the way BoMs are exploded made `mrp_phantom_equiv` horrifically slow and problematic.


Example scenario
----------------

* Chair A is the item sold to a customer
* There are 2 different suppliers for that product - ChairB (supplier 1) and ChairC (supplier 2), which are considered to be "close enough" to be considered as the same product.
* ChairB and ChairC are not simply rolled into ChairA (i.e. setting ChairA with 2 distinct suppliers) in order to aid tracking of supply issues, returns, etc.

Usage
-----

1. Create a product and set "Is Commingled?"
2. On the commingled tab, add the commingled products

