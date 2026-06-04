{
    "name": "product_alternative_sale",
    "summary": "Show a product's alternatives on the sale order line in a popup",
    "author": "Glo Networks",
    "category": "Sales/Sales",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "depends": ["sale", "product_alternative"],
    "data": [
        "views/product_alternative_menus.xml",
        "views/sale_order_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "product_alternative_sale/static/src/**/*",
        ],
    },
    "website": "https://github.com/GlodoUK/odoo-addons",
}
