# Addons for Odoo

This repository houses addons for many areas of Odoo. It is an amalgamation of multiple previous repositories (GlodoUK/sale, web, etc.)

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[concurrency_warning](concurrency_warning/) | 13.0.1.0.0 |  | Issue a concurrency warning and reload the page content if a user has left a model open, and it been altered in the meantime.
[cron_running](cron_running/) | 13.0.1.0.0 |  | Shows if a scheduled action is running
[healthcheck](healthcheck/) | 13.0.1.0.0 |  | Healthcheck for monitoring, etc. Complementary to prometheus module.
[mail_force_sender](mail_force_sender/) | 13.0.1.0.0 |  | Force the outgoing email address, overriding Odoo's default behaviour of using the initiating user's email.
[mail_larger_chatter](mail_larger_chatter/) | 13.0.1.0.0 |  | Adds some utility css classes to increase the size of the chatter.
[mail_shortcode_menu](mail_shortcode_menu/) | 13.0.1.0.0 |  | Adds a menu to edit canned responses without livechat module being installed
[mailgun](mailgun/) | 13.0.1.0.0 |  | Setup the outgoing and incoming mail flow easily by using Mailgun
[sendgrid](sendgrid/) | 13.0.1.0.0 |  | Setup the outgoing and incoming mail through Sendgrid
[stock_picking_validation_warning](stock_picking_validation_warning/) | 13.0.1.0.0 |  | Partner warning on stock picking validation
[web_leaflet](web_leaflet/) | 13.0.1.0.0 |  | Defines an Odoo Enterprise-like Map view

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

Each module can have a totally different license, as long as they adhere to Glo Networks
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.
