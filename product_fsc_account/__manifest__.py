{
    "name": "product_fsc_account",
    "summary": "FSC claim on invoices and bills",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "19.0.1.0.0",
    "depends": ["product_fsc", "account"],
    "data": [
        "report/fsc_report_templates.xml",
        "views/account_move.xml",
    ],
    "license": "LGPL-3",
    "auto_install": ["product_fsc", "account"],
}
