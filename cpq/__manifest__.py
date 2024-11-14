{
    "name": "cpq",
    "summary": "Dynamic Configure-Price-Quote-style generation of products",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales/Sales",
    "version": "17.0.1.0.0",
    "depends": [
        "product",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_template.xml",
        "views/product_product.xml",
        "views/product_attribute.xml",
    ],
    "demo": [],
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            "cpq/static/src/components/**/*",
        ],
    },
}
