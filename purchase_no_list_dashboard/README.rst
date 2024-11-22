==========================
purchase_no_list_dashboard
==========================

On large installations the purchase.order list view can become very slow to load
due to the 15.0 implementation of `retrieve_dashboard` on the `purchase.order`
model.

This was fixed under 16.0, but not backported to 15.0 [1]

This module disables the dashboard header functionality.

[1] https://github.com/odoo/odoo/pull/96921

