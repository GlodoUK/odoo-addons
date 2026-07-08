{
    "name": "product_fsc_sale",
    "summary": "FSC claim on sale orders and invoices",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "19.0.1.0.0",
    "depends": ["product_fsc", "sale", "account"],
    "data": [
        "report/fsc_report_templates.xml",
    ],
    "license": "LGPL-3",
    "auto_install": ["product_fsc", "sale"],
}
