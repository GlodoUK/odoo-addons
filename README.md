# Addons for Odoo

This repository houses addons for many areas of Odoo. It is an amalgamation of multiple previous repositories (GlodoUK/sale, web, etc.)

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_invoice_component_events](account_invoice_component_events/) | 12.0.1.0.0 |  | Account Invoice Component Events
[account_move_line_reconcile_queued](account_move_line_reconcile_queued/) | 12.0.1.1.0 |  | Account move line reconcile queued
[account_payment_better_matching](account_payment_better_matching/) | 12.0.1.1.0 |  | A better interface for bulk, but manual payment matching
[account_payment_better_matching_queued](account_payment_better_matching_queued/) | 12.0.1.0.0 |  | Adds queued support to account_payment_better_matching
[brands](brands/) | 12.0.0.0.2 |  | Allows a sale order and product to be associated with a brand
[brands_crm](brands_crm/) | 12.0.1.0.0 |  | Allows a CRM entry to be associated with a brand
[brands_sale_stock](brands_sale_stock/) | 12.0.1.0.0 |  | Integrates sale_stock with brands
[concurrency_warning](concurrency_warning/) | 12.0.1.0.0 |  | Issue a concurrency warning if a user has left a model open, and it been altered in the meantime.
[connector_edi](connector_edi/) | 12.0.1.0.0 |  | Base EDI module
[connector_edi_envelope_codec_csv](connector_edi_envelope_codec_csv/) | 12.0.1.0.0 |  | EDI Connector - CSV nth Field Envelope Codec
[connector_edi_envelope_codec_edination](connector_edi_envelope_codec_edination/) | 12.0.1.0.0 |  | EDI Connector - EDINation API Envelope Codec
[connector_edi_protocol_mail](connector_edi_protocol_mail/) | 12.0.1.0.0 |  | EDI Mail Protocol Support
[connector_edi_sale](connector_edi_sale/) | 12.0.1.0.0 |  | EDI Sales module
[cron_running](cron_running/) | 12.0.1.0.0 |  | Shows if a scheduled action is running
[delivery_carrier_calendar](delivery_carrier_calendar/) | 12.0.1.0.0 |  | Delivery Carrier Calendar
[healthcheck](healthcheck/) | 12.0.1.0.0 |  | Healthcheck for monitoring, etc. Complementary to prometheus module.
[mail_force_sender](mail_force_sender/) | 12.0.1.1.0 |  | Force the outgoing email address, overriding Odoo's default behaviour of using the initiating user's email.
[mailgun](mailgun/) | 12.0.1.2.0 |  | Setup the outgoing and incoming mail flow easily by using Mailgun
[onchange_helper_inherits](onchange_helper_inherits/) | 12.0.1.1.0 |  | Technical module that eases onchange spec execution.
[procurement_purchase_no_merge](procurement_purchase_no_merge/) | 12.0.1.0.1 |  | Prevent POs merging, create 1:1 relationship for SO:PO
[product_stock_orderpoint_link](product_stock_orderpoint_link/) | 12.0.1.0.0 |  | Adds a smart button on products and templates to go to their reordering rules, and allows reorderpoints to be created from product templates and variants.
[prometheus](prometheus/) | 12.0.1.0.0 |  | Monkey patches Odoo to install prometheus timings for http requests and sql queries.
[purchase_filter_by_receipt_state](purchase_filter_by_receipt_state/) | 12.0.1.0.0 |  | Filter Purchases by receipt state
[queue_job_duration](queue_job_duration/) | 12.0.1.0.0 |  | Adds a time elapsed field to the job queue
[report_ping](report_ping/) | 12.0.1.0.0 |  | report pings
[res_partner_search_create](res_partner_search_create/) | 12.0.1.0.0 |  | Partner utility functions to search or create from values
[sale_order_filter_by_delivery_state](sale_order_filter_by_delivery_state/) | 12.0.1.0.0 |  | Filter sale orders by delivery state.
[sale_product_uom_rounding](sale_product_uom_rounding/) | 12.0.1.0.0 |  | Round sale order line quantities when entered
[sales_person_invoice_no_follow](sales_person_invoice_no_follow/) | 12.0.1.0.0 |  | Don't make the sales person a follower on newly created invoices
[sendgrid](sendgrid/) | 12.0.1.0.0 |  | Setup the outgoing and incoming mail through Sendgrid
[stock_picking_component_events](stock_picking_component_events/) | 12.0.1.0.0 |  | Stock Picking Component Events
[twilio_sms](twilio_sms/) | 12.0.1.0.1 |  | Twilio SMS Gateway
[web_button_enable_with_no_record](web_button_enable_with_no_record/) | 12.0.1.0.1 |  | Allows you to force Odoo to enable a button, even if there is no record
[web_export_verbatim](web_export_verbatim/) | 12.0.1.0.0 |  | web_export_verbatim
[web_higher_upload_limit](web_higher_upload_limit/) | 12.0.1.0.1 |  | Increases the upload limit
[web_many2many_list](web_many2many_list/) | 12.0.1.0.1 |  | Adds a custom many2many as a list, rather than displaying "X Records". This is a Readonly implemented list.
[web_no_swipe](web_no_swipe/) | 12.0.1.0.0 |  | Swipe in v12 is broken on resize. Make it a no-op.
[web_ribbon](web_ribbon/) | 12.0.1.0.0 |  | Backport of the 13.0+ web.ribbon widget. Takes LGPL3 web.ribbon widget from Odoo 13.0 and makes it available to 12.0.
[with_savepoint_decorator](with_savepoint_decorator/) | 12.0.1.0.0 |  | Technical module that provides a with_savepoint decorator

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

Each module can have a totally different license, as long as they adhere to Glo Networks
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.
