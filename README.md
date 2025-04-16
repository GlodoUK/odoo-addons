[![Build Status](https://github.com/GlodoUK/odoo-addons/actions/workflows/test.yml/badge.svg?branch=17.0)](https://github.com/GlodoUK/odoo-addons/actions/workflows/test.yml?query=branch%3A17.0)

# Addons for Odoo

This repository houses addons for many areas of Odoo. It is an amalgamation of multiple previous repositories (GlodoUK/sale, web, etc.)

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[bom_auto_create_components](bom_auto_create_components/) | 17.0.1.0.0 |  | Wizard to create BoM component lines based on matching product attributes
[brands](brands/) | 17.0.1.0.0 |  | Allows a sale order and product to be associated with a brand
[brands_account](brands_account/) | 17.0.1.0.0 |  | Extend brands functionality to account module
[brands_crm](brands_crm/) | 17.0.1.0.0 |  | Allows a CRM entry to be associated with a brand
[brands_sale_stock](brands_sale_stock/) | 17.0.1.0.0 |  | Integrates sale_stock with brands
[connector_edi](connector_edi/) | 17.0.1.0.0 |  | Base EDI module
[connector_edi_protocol_ftp](connector_edi_protocol_ftp/) | 17.0.1.0.0 |  | EDI FTP Protocol Support
[connector_edi_protocol_ssh](connector_edi_protocol_ssh/) | 17.0.1.0.0 |  | EDI SFTP and SCP Protocol Support
[cpq](cpq/) | 17.0.1.0.0 |  | Dynamic Configure-Price-Quote-style generation of products
[cpq_account](cpq_account/) | 17.0.1.0.0 |  | Glue module between CPQ and account
[cpq_banding](cpq_banding/) | 17.0.1.0.0 |  | Banding/Fabric Custom Values
[cpq_mrp](cpq_mrp/) | 17.0.1.1.0 |  | Glue module between CPQ and MRP
[cpq_mrp_account](cpq_mrp_account/) | 17.0.1.1.0 |  | Glue module between CPQ and mrp_account
[cpq_sale](cpq_sale/) | 17.0.1.0.0 |  | Glue module between CPQ and Sale
[cpq_sale_mrp](cpq_sale_mrp/) | 17.0.1.1.0 |  | Glue module for sale_mrp and cpq_mrp
[credit_control](credit_control/) | 17.0.0.0.0 |  | Credit Control Policies
[glo_checklists](glo_checklists/) | 17.0.1.0.0 |  | Add checklists to any model via a template.
[glo_commercial_invoice](glo_commercial_invoice/) | 17.0.1.0.0 |  | Glo Commercial Invoice
[product_simple_variant_builder](product_simple_variant_builder/) | 17.0.1.0.0 |  | Simple wizard to build dynamic variants from a product template
[product_supplier_info_apply_on_variants](product_supplier_info_apply_on_variants/) | 17.0.1.0.0 |  | Apply on Variants for product.supplierinfo records
[purchase_order_line_sequence_simple](purchase_order_line_sequence_simple/) | 17.0.1.0.0 |  | Purchase Order Line Sequence Simple
[purchase_stock_update_move_date](purchase_stock_update_move_date/) | 17.0.1.0.0 |  | Purchase Stock Update Move Date
[purchase_to_invoice_menu](purchase_to_invoice_menu/) | 17.0.0.0.0 |  | Adds a 'To Invoice' menu to the Purchase menu
[report_layout_no_header_no_footer](report_layout_no_header_no_footer/) | 17.0.1.0.0 |  | Report Layout No Header No Footer
[sale_force_manual_delivered](sale_force_manual_delivered/) | 17.0.1.0.0 |  | Allow forced manual delivery
[sale_pricelist_customer_ref](sale_pricelist_customer_ref/) | 17.0.1.0.0 |  | Adds customer ref field to pricelist item.
[stock_picking_move_form](stock_picking_move_form/) | 17.0.1.0.0 |  | Adds a button to the stock.picking form view to easily show the stock.move form
[stock_picking_validation_warning](stock_picking_validation_warning/) | 17.0.1.0.0 |  | Partner warning on stock picking validation
[stock_pre_reserve](stock_pre_reserve/) | 17.0.1.1.0 |  | Link an existing outbound move to a new inbound move manually, allowing reservations against inbound stock.
[website_sale_require_login](website_sale_require_login/) | 17.0.1.0.0 |  | Require login on the eCommerce pages

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

Each module can have a totally different license, as long as they adhere to Glo Networks
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.
