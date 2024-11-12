{
    "name": "stock_available_sale_stock",
    "summary": "Integrates stock_available and sale_stock",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/stock-delivery",
    "category": "Uncategorized",
    "version": "15.0.1.0.0",
    "depends": ["stock_available", "sale_stock"],
    "auto_install": True,
    "data": [
        "views/sale.xml",
    ],
    "demo": [],
    "license": "AGPL-3",
    "assets": {
        "web.assets_backend": [
            "stock_available_sale_stock/static/src/js/**/*",
        ],
        "web.assets_qweb": [
            "stock_available_sale_stock/static/src/xml/**/*",
        ],
    },
}
