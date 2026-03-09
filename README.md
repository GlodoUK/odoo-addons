[![Build Status](https://github.com/GlodoUK/odoo-addons/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/GlodoUK/odoo-addons/actions/workflows/test.yml?query=branch%3A14.0)

# Addons for Odoo

This repository houses addons for many areas of Odoo. It is an amalgamation of multiple previous repositories (GlodoUK/sale, web, etc.)

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_invoice_component_events](account_invoice_component_events/) | 14.0.1.0.0 |  | Account Invoice Component Events
[account_journal_restrict_by_user](account_journal_restrict_by_user/) | 14.0.1.0.0 |  | Account Journal Restriction by Users
[account_quarter_date](account_quarter_date/) | 14.0.1.0.1 |  | Generate Quarters based on the fiscal period
[brands](brands/) | 14.0.1.0.0 |  | Allows a sale order and product to be associated with a brand
[brands_crm](brands_crm/) | 14.0.0.1.0 |  | Allows a CRM entry to be associated with a brand
[concurrency_warning](concurrency_warning/) | 14.0.1.0.0 |  | Issue a concurrency warning and reload the page content if a user has left a model open, and it been altered in the meantime.
[connector_edi](connector_edi/) | 14.0.1.0.0 |  | Base EDI module
[connector_edi_excel](connector_edi_excel/) | 14.0.1.0.0 |  | Add Pandas cokpatibility to connector_edi fpr Excel files ONLY
[connector_edi_protocol_ftp](connector_edi_protocol_ftp/) | 14.0.1.0.0 |  | EDI FTP Protocol Support
[connector_edi_protocol_mail](connector_edi_protocol_mail/) | 14.0.1.0.0 |  | EDI Mail Protocol Support
[connector_edi_sale](connector_edi_sale/) | 14.0.1.0.0 |  | EDI Sales module
[credit_control](credit_control/) | 14.0.1.0.0 |  | Credit Control Policies
[delivery_state_events](delivery_state_events/) | 14.0.1.0.1 |  | Provides fields and methods to support tracking a shipment
[glodo_client](glodo_client/) | 14.0.1.0.0 |  | Server-wide client for Glodo Cloud remote instance management
[healthcheck](healthcheck/) | 14.0.1.0.0 |  | Healthcheck for monitoring, etc. Complementary to prometheus module.
[mail_force_sender](mail_force_sender/) | 14.0.1.0.0 |  | Force the outgoing email address, overriding Odoo's default behaviour of using the initiating user's email.
[mailgun](mailgun/) | 14.0.1.0.0 |  | Setup the outgoing and incoming mail flow easily by using Mailgun
[partner_extra_phone](partner_extra_phone/) | 14.0.1.0.0 |  | Adds multiple phone numbers to Contacts
[partner_social_media](partner_social_media/) | 14.0.1.0.0 |  | Adds social media information on partner
[purchase_partner_journal](purchase_partner_journal/) | 14.0.1.0.1 |  | Supplier forces Invoice Journal
[res_partner_search_create](res_partner_search_create/) | 14.0.1.0.0 |  | Partner utility functions to search or create from values
[res_partner_warehouse](res_partner_warehouse/) | 14.0.1.0.0 |  | Partner 'Virtual' Warehouses
[sale_lease_stock](sale_lease_stock/) | 14.0.1.0.0 |  | Leasing using Stock (rental-lite)
[sendgrid](sendgrid/) | 14.0.1.0.0 |  | Setup the outgoing and incoming mail through Sendgrid
[stock_picking_component_events](stock_picking_component_events/) | 14.0.1.0.0 |  | Stock Picking Component Events
[twilio_sms](twilio_sms/) | 14.0.1.0.0 |  | Twilio SMS Gateway
[web_html_code_view](web_html_code_view/) | 14.0.1.1.0 |  | Enables Code View in Web Editor for all users
[website_sale_lease_stock](website_sale_lease_stock/) | 14.0.1.0.1 |  | Leasing: Integrates sale_stock_lease with website_sale
[website_sale_lease_stock_one_period](website_sale_lease_stock_one_period/) | 14.0.1.0.0 |  | website_sale_lease_stock: Permit only allows 1 lease period per sale order via the website

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

Each module can have a totally different license, as long as they adhere to Glo Networks
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.
