{
    "name": "cpq_sale",
    "summary": "Glue module between CPQ and Sale",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "15.0.1.0.0",
    "depends": ["cpq", "sale", "sale_product_configurator"],
    "auto_install": ["cpq", "sale"],
    "data": [
        "views/sale_order.xml",
        "views/product_template.xml",
    ],
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            "cpq_sale/static/src/js/product_configurator_widget.esm.js",
        ],
    },
}
