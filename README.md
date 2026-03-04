[![Build Status](https://github.com/GlodoUK/odoo-addons/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/GlodoUK/odoo-addons/actions/workflows/test.yml?query=branch%3A18.0)

# Addons for Odoo

This repository houses addons for many areas of Odoo. It is an amalgamation of multiple previous repositories (GlodoUK/sale, web, etc.)

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_invoice_component_events](account_invoice_component_events/) | 18.0.1.0.0 |  | Account Invoice Component Events
[auth_oauth_restrict_website](auth_oauth_restrict_website/) | 18.0.1.0.0 |  | Restrict certain OAuth providers from display
[automate_customer_lead_time](automate_customer_lead_time/) | 18.0.1.0.0 |  | Automatically modify lead times on sales for vendor lead time
[brands](brands/) | 18.0.1.0.0 |  | Brands
[brands_sale_stock](brands_sale_stock/) | 18.0.1.0.0 |  | Brands Sale Stock
[concurrency_warning](concurrency_warning/) | 18.0.1.0.0 |  | Issue a visual warning and reload the page content if a user has left a model open, and it been altered in the meantime.
[connector_edi](connector_edi/) | 18.0.1.0.0 |  | Base EDI module
[connector_edi_excel](connector_edi_excel/) | 18.0.1.0.0 |  | connector_edi_excel
[connector_edi_product](connector_edi_product/) | 18.0.1.0.0 |  | Connector EDI Product
[connector_edi_protocol_ftp](connector_edi_protocol_ftp/) | 18.0.1.0.0 |  | EDI FTP Protocol Support
[connector_edi_protocol_mail](connector_edi_protocol_mail/) | 18.0.1.0.0 |  | EDI Mail Protocol Support
[connector_edi_protocol_ssh](connector_edi_protocol_ssh/) | 18.0.1.0.0 |  | EDI SFTP and SCP Protocol Support
[connector_edi_sale](connector_edi_sale/) | 18.0.1.0.0 |  | Connector EDI Sale
[connector_edi_stock](connector_edi_stock/) | 18.0.1.0.0 |  | Connector EDI Stock
[credit_control](credit_control/) | 18.0.1.0.1 |  | Credit Control Policies
[delivery_carrier_match_sale_order_value](delivery_carrier_match_sale_order_value/) | 18.0.1.0.0 |  | Ensure that a carrier can only be used when sale order total is less than a given amount
[delivery_carrier_validation](delivery_carrier_validation/) | 18.0.1.0.0 |  | Utility module to add a validation step before send_to_shipper
[delivery_parcelhub_whistl](delivery_parcelhub_whistl/) | 18.0.1.0.0 |  | Connector to integrate with Parcelhub/Whistl courier
[delivery_spring](delivery_spring/) | 18.0.1.0.0 |  | Connector to integrate with Spring courier
[delivery_state_events](delivery_state_events/) | 18.0.1.0.0 |  | Provides fields and methods to support tracking a shipment
[forwardport_stock_mts_else_mto_link](forwardport_stock_mts_else_mto_link/) | 18.0.1.0.0 |  | Reverts the behaviour changed in Odoo where mts_else_mto orders are not fully linked
[glo_checklists](glo_checklists/) | 18.0.1.0.0 |  | Add checklists to any model via a template.
[glo_checklists_account_accountant](glo_checklists_account_accountant/) | 18.0.1.0.0 |  | Glue module to fix a compatibility issue between Checklist Anything and account_accountant
[glodo_client](glodo_client/) | 18.0.1.0.0 |  | Server-wide client for Glodo Cloud remote instance management
[helpdesk_account_move_link](helpdesk_account_move_link/) | 18.0.1.0.0 |  | Helpdesk Account Move Link
[helpdesk_commercial_partner](helpdesk_commercial_partner/) | 18.0.1.0.0 |  | Helpdesk Ticket Commercial Partner
[helpdesk_portal_new_ticket](helpdesk_portal_new_ticket/) | 18.0.1.0.0 |  | Helpdesk Portal New Ticket
[helpdesk_portal_new_ticket_category](helpdesk_portal_new_ticket_category/) | 18.0.1.0.0 |  | helpdesk_portal_new_ticket_category
[helpdesk_portal_new_ticket_privacy](helpdesk_portal_new_ticket_privacy/) | 18.0.1.0.0 |  | Helpdesk Portal New Ticket
[helpdesk_portal_new_ticket_ticket_type_properties](helpdesk_portal_new_ticket_ticket_type_properties/) | 18.0.1.0.0 |  | Website Helpdesk Ticket Create Ticket Type Properties
[helpdesk_portal_reopen](helpdesk_portal_reopen/) | 18.0.1.0.0 |  | Helpdesk Portal Reopen
[helpdesk_privacy](helpdesk_privacy/) | 18.0.1.0.0 |  | Helpdesk Privacy
[helpdesk_purchase_order_link](helpdesk_purchase_order_link/) | 18.0.1.0.0 |  | Helpdesk Purchase Order Link
[helpdesk_sale_order_account_move_link](helpdesk_sale_order_account_move_link/) | 18.0.1.0.0 |  | Helpdesk Sale Order Account Move Link
[helpdesk_sale_order_generator](helpdesk_sale_order_generator/) | 18.0.1.0.0 |  | Generates Quotation from helpdesk
[helpdesk_sale_order_link](helpdesk_sale_order_link/) | 18.0.1.0.0 |  | Helpdesk Sale Order Link
[helpdesk_ticket_category](helpdesk_ticket_category/) | 18.0.1.0.0 |  | Helpdesk Ticket Category
[helpdesk_ticket_escalate](helpdesk_ticket_escalate/) | 18.0.1.0.0 |  | Helpdesk Ticket Escalate
[helpdesk_ticket_merge](helpdesk_ticket_merge/) | 18.0.1.0.0 |  | Merge helpdesk tickets including all ticktet history and attachments.
[helpdesk_ticket_type_properties](helpdesk_ticket_type_properties/) | 18.0.1.0.0 |  | Helpdesk Ticket Type Properties
[mail_postmark_email_header](mail_postmark_email_header/) | 18.0.1.0.0 |  | Mail Postmark Email Header
[maintenance_request_template](maintenance_request_template/) | 18.0.1.0.0 |  | maintenance_request_template
[perf_website_sale](perf_website_sale/) | 18.0.1.0.0 |  | A collection of performance improvements for website_sale under 18.0
[product_variant_exclusion](product_variant_exclusion/) | 18.0.1.0.0 |  | Short (1 phrase/line) summary of the module's purpose
[product_variant_specific_tax_purchase](product_variant_specific_tax_purchase/) | 18.0.1.0.0 |  | product_variant_specific_tax_purchase
[product_variant_specific_tax_sale](product_variant_specific_tax_sale/) | 18.0.1.0.0 |  | product_variant_specific_tax_sale
[purchase_minimum_value](purchase_minimum_value/) | 18.0.1.0.0 |  | Restrict minimum purchase order value
[res_partner_bank_display_format](res_partner_bank_display_format/) | 18.0.1.0.0 |  | Customise the format of the partner bank
[res_partner_search_create](res_partner_search_create/) | 18.0.1.0.0 |  | Partner utility functions to search or create from values
[sale_force_manual_delivered](sale_force_manual_delivered/) | 18.0.1.0.0 |  | sale_force_manual_delivered
[sale_order_hold](sale_order_hold/) | 18.0.1.0.0 |  | Adds the ability to put sale orders on hold
[sale_order_hold_stock_picking_hold](sale_order_hold_stock_picking_hold/) | 18.0.1.0.0 |  | Integrate sale_order_hold with stock_picking_hold
[sale_stock_force_pdf_download](sale_stock_force_pdf_download/) | 18.0.1.0.0 |  | Sale Stock Force PDF Download
[sendgrid](sendgrid/) | 18.0.1.0.0 |  | Handle Inbound Email through Sendgrid Webhooks
[stock_available_sale_stock](stock_available_sale_stock/) | 18.0.1.0.0 |  | Stock Available Sale Stock
[stock_picking_component_events](stock_picking_component_events/) | 18.0.1.0.0 |  | Stock Picking Component Events
[stock_picking_hold](stock_picking_hold/) | 18.0.1.0.0 |  | Adds the ability to put stock pickings on hold
[web_cmd_search](web_cmd_search/) | 18.0.1.0.0 |  | Adds a global command search to quick access records

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

Each module can have a totally different license, as long as they adhere to Glo Networks
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

asd
