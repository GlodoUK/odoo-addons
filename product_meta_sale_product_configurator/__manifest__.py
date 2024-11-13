{
    "name": "product_meta_configurator",
    "summary": "Glue module between sale_product_configurator and product_meta",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    "version": "15.0.1.0.0",
    "depends": [
        "product_meta_sale",
        "base_sparse_field",
        "sale_product_configurator",
    ],
    "data": [
        "views/product_template.xml",
        "views/sale_product_configurator_templates.xml",
        "views/sale_order.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "product_meta_sale_product_configurator/static/src/js/product_configurator_modal.js",  # noqa: B950
            "product_meta_sale_product_configurator/static/src/js/product_configurator_widget.js",  # noqa: B950
        ],
    },
    "license": "AGPL-3",
}
