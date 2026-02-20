{
    "name": "stock_barcode_putaway_rules",
    "summary": "Add a button on the barcode app to evaluate putaway rules",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "15.0.1.0.0",
    "depends": ["stock_barcode"],
    "assets": {
        "web.assets_backend": [
            "stock_barcode_putaway_rules/static/src/**/*.js",
        ],
        "web.assets_qweb": [
            "stock_barcode_putaway_rules/static/src/**/*.xml",
        ],
    },
    "data": [
        "views/stock_picking_type.xml",
    ],
    "license": "LGPL-3",
}
