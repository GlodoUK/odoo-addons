{
    "name": "cpq_sale",
    "summary": "Glue module between CPQ and Sale",
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "auto_install": ["cpq", "sale"],
    "depends": ["cpq", "sale"],
    "data": [
        "views/product_attribute_cpq_group.xml",
        "views/product_template.xml",
        "views/sale_order.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cpq_sale/static/src/js/product_configurator_widget.esm.js",
        ],
    },
    "license": "LGPL-3",
}
