{
    "name": "sale_order_hold",
    "summary": "Adds the ability to put sales onto hold",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    "version": "15.0.1.0.0",
    "depends": ["sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order.xml",
        "wizards/sale_hold.xml",
        "wizards/sale_unhold.xml",
        "data/sale_order_hold_reasons.xml",
    ],
    "license": "LGPL-3",
}
