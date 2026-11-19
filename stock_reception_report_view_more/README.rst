================================
stock_reception_report_view_more
================================

Backport of the Odoo 20.0 "View More" button on the allocation (reception)
report.

Odoo 19.0 only lists the transfers waiting for a product while the receipt's
quantity lasts, earliest first. This module adds a **View More** button that
also lists the later transfers still waiting for the product, so a receipt can
be allocated to one of those instead.

* Extra lines show the quantity the transfer is waiting for, capped at what
  the receipt still has unallocated.
* **Assign All** never assigns extra lines; assign them one at a time.
* Assigning is refused if it would link more than the receipt has left
  unlinked, so the same stock cannot go to two transfers.
* The printed report is unchanged.
