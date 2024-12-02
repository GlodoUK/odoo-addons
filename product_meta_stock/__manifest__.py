{
    "name": "product_meta_stock",
    "summary": "Glue module between product_meta and stock",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Inventory",
    "version": "15.0.1.0.0",
    "depends": ["stock", "product_meta"],
    "auto_install": True,
    "data": ["security/ir.model.access.csv", "views/product_template.xml"],
    "license": "AGPL-3",
}
