------------
cpq_sale_mrp
------------

Glue module between sale_mrp and cpq_mrp.

Known Issues
------------

`_compute_qty_delivered` and `_get_qty_procurement` both work on the ultra basic
assumptions around quantities.

This is partially by design, until we have a better solution.

As products are *highly* configurable and BoMs may change over time, this seems
like the least disruptive solution, for the moment.

