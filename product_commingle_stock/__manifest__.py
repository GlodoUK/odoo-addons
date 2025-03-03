{
    "name": "product_commingle_stock",
    "summary": """product_commingle <-> stock glue module""",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "15.0.1.2.0",
    "depends": ["product_commingle", "stock"],
    "auto_install": True,
    "data": [
        "security/ir.model.access.csv",
        "views/stock_picking.xml",
        "views/product_template.xml",
        "views/product_commingled.xml",
    ],
    "license": "AGPL-3",
}
