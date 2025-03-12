[![Pre-commit Status](https://github.com/GlodoUK/odoo-addons/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/GlodoUK/odoo-addons/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/GlodoUK/odoo-addons/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/GlodoUK/odoo-addons/actions/workflows/test.yml?query=branch%3A16.0)

# Addons for Odoo

This repository houses addons for many areas of Odoo. It is an amalgamation of multiple previous repositories (GlodoUK/sale, web, etc.)

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_invoice_component_events](account_invoice_component_events/) | 16.0.1.0.0 |  | Account Invoice Component Events
[auth_oauth_restrict_website](auth_oauth_restrict_website/) | 16.0.1.0.0 |  | Restrict certain OAuth providers from display
[backport_mail_tracking_duration_mixin](backport_mail_tracking_duration_mixin/) | 16.0.1.0.0 |  | Backport of the mail.tracking.duration.mixin from 17.0
[concurrency_warning](concurrency_warning/) | 16.0.1.0.0 |  | Issue a visual warning and reload the page content if a user has left a model open, and it been altered in the meantime.
[connector_edi](connector_edi/) | 16.0.1.0.3 |  | Base EDI module
[connector_edi_magento](connector_edi_magento/) | 16.0.1.0.0 |  | EDI integrations for Magento
[connector_edi_product](connector_edi_product/) | 16.0.1.0.0 |  | EDI Product Module
[connector_edi_res_partner](connector_edi_res_partner/) | 16.0.1.0.0 |  | EDI Partner binding module
[connector_edi_sale](connector_edi_sale/) | 16.0.1.0.0 |  | EDI Sales module
[credit_control](credit_control/) | 16.0.1.0.0 |  | Credit Control Policies
[crm_stage_duration](crm_stage_duration/) | 16.0.0.0.0 |  | Monitors and adds stage duration on kanban and tree views, and also the chatter
[sendgrid](sendgrid/) | 16.0.1.0.0 |  | Handle Inbound Email through Sendgrid Webhooks
[stock_picking_component_events](stock_picking_component_events/) | 16.0.1.0.0 |  | Stock Picking Component Events
[twilio_sms](twilio_sms/) | 16.0.2.0.0 |  | Twilio SMS Gateway
[web_cmd_search](web_cmd_search/) | 16.0.1.0.0 |  | Adds a global command search to quick access records
[web_list_min_width](web_list_min_width/) | 16.0.1.0.0 |  | Support min-width on a list column

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

Each module can have a totally different license, as long as they adhere to Glo Networks
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.
