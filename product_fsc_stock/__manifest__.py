{
    "name": "product_fsc_stock",
    "summary": "FSC claim on delivery documents",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "19.0.1.0.0",
    "depends": ["product_fsc", "stock"],
    "data": [
        "report/report_deliveryslip.xml",
    ],
    "license": "LGPL-3",
    "auto_install": ["product_fsc", "stock"],
}
