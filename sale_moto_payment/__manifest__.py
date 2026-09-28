{
    "name": "Sale MOTO Payment",
    "summary": "Phone-payment popup with inline payment form for confirmed sale orders",
    "author": "Glo Networks",
    "category": "Sales",
    "version": "19.0.1.0.0",
    "depends": [
        "sale",
        "payment",
    ],
    "data": [
        "views/sale_order_views.xml",
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sale_moto_payment/static/src/js/moto_payment.esm.js",
        ],
    },
    "license": "LGPL-3",
    "website": "https://github.com/GlodoUK/odoo-addons",
}
