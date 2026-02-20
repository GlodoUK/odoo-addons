[![Build Status](https://github.com/GlodoUK/odoo-addons/actions/workflows/test.yml/badge.svg?branch=15.0)](https://github.com/GlodoUK/odoo-addons/actions/workflows/test.yml?query=branch%3A15.0)

# Addons for Odoo

This repository houses addons for many areas of Odoo. It is an amalgamation of multiple previous repositories (GlodoUK/sale, web, etc.)

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_invoice_component_events](account_invoice_component_events/) | 15.0.1.0.0 |  | Account Invoice Component Events
[account_move_allow_bank_journals](account_move_allow_bank_journals/) | 15.0.1.0.0 |  | Allow journal entries to be posted to account.journal of type=bank
[account_move_line_reconcile_queued](account_move_line_reconcile_queued/) | 15.0.1.0.0 |  | Account move line reconcile queued
[account_move_restrict_reset_to_draft](account_move_restrict_reset_to_draft/) | 15.0.1.0.0 |  | Reset users who can push the 'reset to draft' button on an account.move
[account_payment_better_matching](account_payment_better_matching/) | 15.0.1.1.0 |  | A better interface for bulk, but manual payment matching
[account_payment_better_matching_queued](account_payment_better_matching_queued/) | 15.0.1.0.0 |  | Adds queued support to account_payment_better_matching
[auth_signup_optional_notify](auth_signup_optional_notify/) | 15.0.1.0.0 |  | Optionally disable the notification on user login
[backport_stock_barcode_manual_scan](backport_stock_barcode_manual_scan/) | 15.0.1.0.0 |  | Manually scan a barcode
[backport_stock_removal_least_packages](backport_stock_removal_least_packages/) | 15.0.1.0.0 |  | Backport 'least packages' stock removal strategy
[brands](brands/) | 15.0.2.0.0 |  | Allows a sale order and product to be associated with a brand
[brands_crm](brands_crm/) | 15.0.0.1.0 |  | Allows a CRM entry to be associated with a brand
[brands_sale_stock](brands_sale_stock/) | 15.0.0.1.0 |  | Integrates sale_stock with brands
[concurrency_warning](concurrency_warning/) | 15.0.1.0.0 |  | Issue a visual warning and reload the page content if a user has left a model open, and it been altered in the meantime.
[connector_edi](connector_edi/) | 15.0.3.0.1 |  | Base EDI module
[connector_edi_excel](connector_edi_excel/) | 15.0.1.0.0 |  | Add Pandas cokpatibility to connector_edi fpr Excel files ONLY
[connector_edi_pandas](connector_edi_pandas/) | 15.0.1.0.0 |  | Add Pandas to the connector_edi safe_eval context
[connector_edi_product](connector_edi_product/) | 15.0.1.0.0 |  | EDI Product module
[connector_edi_protocol_ftp](connector_edi_protocol_ftp/) | 15.0.1.0.0 |  | EDI FTP Protocol Support
[connector_edi_protocol_mail](connector_edi_protocol_mail/) | 15.0.1.0.0 |  | EDI Mail Protocol Support
[connector_edi_protocol_ssh](connector_edi_protocol_ssh/) | 15.0.1.0.0 |  | EDI SFTP and SCP Protocol Support
[connector_edi_sale](connector_edi_sale/) | 15.0.1.0.0 |  | EDI Sales module
[connector_edi_stock](connector_edi_stock/) | 15.0.1.0.0 |  | Stock Picking Events EDI integration
[cpq](cpq/) | 15.0.1.1.0 |  | Dynamic Configure-Price-Quote-style generation of products
[cpq_account](cpq_account/) | 15.0.1.0.0 |  | Glue module between CPQ and account
[cpq_banding](cpq_banding/) | 15.0.1.0.0 |  | Banding/Fabric Custom Values
[cpq_mrp](cpq_mrp/) | 15.0.1.0.0 |  | Glue module between CPQ and MRP
[cpq_mrp_account](cpq_mrp_account/) | 15.0.1.0.0 |  | Glue module between CPQ and mrp_account
[cpq_sale](cpq_sale/) | 15.0.1.0.0 |  | Glue module between CPQ and Sale
[cpq_sale_mrp](cpq_sale_mrp/) | 15.0.1.0.0 |  | Glue module for sale_mrp and cpq_mrp
[credit_control](credit_control/) | 15.0.1.0.0 |  | Credit Control Policies
[delivery_force_delivery_line](delivery_force_delivery_line/) | 15.0.1.0.0 |  | Summary
[delivery_parcelhub_whistl](delivery_parcelhub_whistl/) | 15.0.1.0.0 |  | Connector to integrate with Parcelhub/Whistl courier
[delivery_spring](delivery_spring/) | 15.0.2.1.0 |  | Connector to integrate with Spring courier
[delivery_state_events](delivery_state_events/) | 15.0.1.0.1 |  | Provides fields and methods to support tracking a shipment
[helpdesk_canned_response](helpdesk_canned_response/) | 15.0.1.0.1 |  | Adds a menu to edit canned responses from within Helpdesk
[helpdesk_rules](helpdesk_rules/) | 15.0.1.0.0 |  | Helpdesk - Automatically apply rules
[helpdesk_sale_order_generator](helpdesk_sale_order_generator/) | 15.0.1.0.1 |  | Generates Quotation from helpdesk
[helpdesk_sale_order_link](helpdesk_sale_order_link/) | 15.0.1.0.2 |  | Links Sales Orders to Helpdesk Tickets
[inventory_adjustment_reason](inventory_adjustment_reason/) | 15.0.0.0.0 |  | Add a note for reason for inventory adjustment
[mail_res_partner_forward](mail_res_partner_forward/) | 15.0.1.0.0 |  | Rule based forwarding of email to other partners
[product_commingle](product_commingle/) | 15.0.1.1.0 |  | Product Commingling
[product_commingle_mrp](product_commingle_mrp/) | 15.0.1.0.0 |  | product_commingle <-> mrp glue module
[product_commingle_purchase_stock](product_commingle_purchase_stock/) | 15.0.1.0.0 |  | Integrates product_commingle and purchase_stock
[product_commingle_sale_stock](product_commingle_sale_stock/) | 15.0.1.0.0 |  | Integrates product_commingle and sale_stock
[product_commingle_stock](product_commingle_stock/) | 15.0.1.2.0 |  | product_commingle <-> stock glue module
[product_commingle_stock_available](product_commingle_stock_available/) | 15.0.1.0.0 |  | product_commingle_stock <-> OCA/stock_available glue module
[product_meta](product_meta/) | 15.0.1.0.0 |  | Adds a 'Meta' (read: pack or combo) Product type.
[product_meta_sale](product_meta_sale/) | 15.0.1.0.0 |  | Glue module between product_meta and sale
[product_meta_sale_product_configurator](product_meta_sale_product_configurator/) | 15.0.1.0.0 |  | Glue module between sale_product_configurator and product_meta
[product_meta_sale_stock](product_meta_sale_stock/) | 15.0.1.0.0 |  | Glue module between product_meta and product_meta_sale_stock
[product_meta_stock](product_meta_stock/) | 15.0.1.0.0 |  | Glue module between product_meta and stock
[product_supplier_info_apply_on_variants](product_supplier_info_apply_on_variants/) | 15.0.1.0.0 |  | Apply on Variants for product.supplierinfo records
[purchase_invoice_legacy](purchase_invoice_legacy/) | 15.0.1.0.0 |  | Restores 12.0 style invoicing to purchase orders
[purchase_invoice_partner](purchase_invoice_partner/) | 15.0.1.0.0 |  | Purchase Invoices are raised against partner rather than the partner invoicing partner
[purchase_minimum_value](purchase_minimum_value/) | 15.0.1.0.0 |  | Restrict minimum purchase order value
[purchase_no_list_dashboard](purchase_no_list_dashboard/) | 15.0.1.0.0 |  | Disable the purchase list dashboard
[purchase_to_invoice_menu](purchase_to_invoice_menu/) | 15.0.1.1.0 |  | Adds a 'To Invoice' menu to the Purchase menu
[res_partner_search_create](res_partner_search_create/) | 15.0.1.0.0 |  | Partner utility functions to search or create from values
[res_partner_warehouse](res_partner_warehouse/) | 15.0.1.0.0 |  | Partner 'Virtual' Warehouses
[sale_confirm_prompt_delivery](sale_confirm_prompt_delivery/) | 15.0.1.0.0 |  | Prompt users to add delivery to a sale, if it's missing
[sale_force_manual_delivered](sale_force_manual_delivered/) | 15.0.2.0.0 |  | Allow forced manual delivery
[sale_order_alternative_products](sale_order_alternative_products/) | 15.0.2.0.0 |  | Module to propose alternative products at the time of Sale Order Line product selection.
[sale_order_hold](sale_order_hold/) | 15.0.1.0.0 |  | Adds the ability to put sales onto hold
[sale_order_hold_stock_picking_hold](sale_order_hold_stock_picking_hold/) | 15.0.1.0.0 |  | Integrates sale_order_hold with stock_picking_hold
[sale_pricelist_customer_ref](sale_pricelist_customer_ref/) | 15.0.1.0.0 |  | Adds customer ref field to pricelist item.
[sale_product_uom_rounding](sale_product_uom_rounding/) | 15.0.1.0.0 |  | Round sale order line quantities when entered
[sale_stock_force_pdf_download](sale_stock_force_pdf_download/) | 15.0.1.0.0 |  | Sale Stock Force PDF Download
[sendgrid](sendgrid/) | 15.0.1.0.0 |  | Handle Inbound Email through Sendgrid Webhooks
[stock_available_sale_stock](stock_available_sale_stock/) | 15.0.1.0.0 |  | Integrates stock_available and sale_stock
[stock_barcode_putaway_rules](stock_barcode_putaway_rules/) | 15.0.1.0.0 |  | Add a button on the barcode app to evaluate putaway rules
[stock_location_freeze](stock_location_freeze/) | 15.0.1.0.2 |  | Prevent further movements of stock in a given location
[stock_picking_component_events](stock_picking_component_events/) | 15.0.1.0.0 |  | Stock Picking Component Events
[stock_picking_hold](stock_picking_hold/) | 15.0.2.0.0 |  | Adds a custom hold state to stock.pickings which prevents deliveries from being processed
[stock_picking_move_form](stock_picking_move_form/) | 15.0.1.0.0 |  | Adds a button to the stock.picking form view to easily show the stock.move form
[stock_picking_validation_warning](stock_picking_validation_warning/) | 15.0.1.0.0 |  | Partner warning on stock picking validation
[stock_pre_reserve](stock_pre_reserve/) | 15.0.1.0.0 |  | Link an existing outbound move to a new inbound move manually, allowing reservations against inbound stock.
[twilio_sms](twilio_sms/) | 15.0.2.0.0 |  | Twilio SMS Gateway
[web_list_min_width](web_list_min_width/) | 15.0.1.0.0 |  | Support min-width on a list column
[web_no_form_quick_edit](web_no_form_quick_edit/) | 15.0.1.0.0 |  | Disable quick edit in form views
[website_leaflet](website_leaflet/) | 15.0.1.0.1 |  | Adds a leaflet.js powered map (eventually snippet)

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

Each module can have a totally different license, as long as they adhere to Glo Networks
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.
