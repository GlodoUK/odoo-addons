{
    "name": "product_fsc_purchase",
    "summary": "FSC claim on purchase orders and requests for quotation",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "19.0.1.0.0",
    "depends": ["product_fsc_account", "purchase"],
    "data": [
        "report/fsc_report_templates.xml",
        "views/purchase_order.xml",
    ],
    "license": "LGPL-3",
    "auto_install": ["product_fsc_account", "purchase"],
}
