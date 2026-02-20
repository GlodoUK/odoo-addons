{
    "name": "stock_location_freeze",
    "summary": "Prevent further movements of stock in a given location",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "15.0.1.0.2",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/freeze_views.xml",
        "views/stock_location.xml",
    ],
    "license": "LGPL-3",
}
