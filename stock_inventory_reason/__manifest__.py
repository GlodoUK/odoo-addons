{
    "name": "stock_inventory_reason",
    "summary": "Always prompt for an inventory adjustment reason when applying a single"
    " Physical Inventory line",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Inventory",
    "version": "19.0.1.0.0",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "security/stock_inventory_adjustment_reason_security.xml",
        "views/stock_inventory_adjustment_reason_views.xml",
        "views/stock_quant_views.xml",
        "wizard/stock_inventory_adjustment_name_views.xml",
    ],
    "demo": [],
    "license": "Other proprietary",
}
