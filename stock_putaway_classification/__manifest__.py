{
    "name": "stock_putaway_classification",
    "summary": "Put-away rules by product classification, one pick face per product",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Inventory/Inventory",
    "version": "19.0.1.0.0",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_classification_views.xml",
        "views/product_views.xml",
        "views/stock_putaway_rule_views.xml",
        "views/stock_storage_category_views.xml",
    ],
    "license": "Other proprietary",
}
