{
    "name": "sale_invoice_consolidation",
    "summary": "Invoicing policy",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "version": "19.0.1.2.0",
    "depends": ["sale", "account"],
    "data": [
        "data/cron.xml",
        "views/res_config_settings.xml",
        "views/res_partner.xml",
        "views/sale_order.xml",
    ],
    "license": "LGPL-3",
}
