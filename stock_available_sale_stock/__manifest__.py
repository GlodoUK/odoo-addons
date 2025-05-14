{
    "name": "Stock Available Sale Stock",
    "version": "18.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "auto_install": True,
    "depends": ["stock_available", "sale_stock"],
    "data": ["views/sale_order_views.xml"],
    "assets": {
        "web.assets_backend": [
            "stock_available_sale_stock/static/src/widgets/*.esm.js",
            "stock_available_sale_stock/static/src/widgets/*.xml",
        ],
    },
    "license": "AGPL-3",
}
