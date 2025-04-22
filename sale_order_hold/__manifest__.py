{
    "name": "Sale Order Hold",
    "summary": "Adds the ability to put sale orders on hold",
    "version": "18.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    "depends": ["sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/sale_order_hold_reason_data.xml",
        "views/sale_order_views.xml",
        "wizards/sale_hold_views.xml",
        "wizards/sale_unhold_views.xml",
    ],
    "license": "LGPL-3",
}
