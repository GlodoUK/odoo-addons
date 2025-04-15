========================== website_sale_require_login ==========================

Enforce login requirement on specific website_sale (read: ecommerce endpoints).

# Why not OCA/website_require_login?

1. We've experienced performance penalties in older versions of Odoo which at the time
   were attributed to website_require_login.
2. We've experienced users incorrectly mis-configuring website_require_login and locking
   themselves out of the website entirely.
3. We've forward ported them from a 14.0 installation.

This module mitigates both issues at the expense of making the porting process
_slightly_ more intensive.
