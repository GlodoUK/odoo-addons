{
    "name": "cpq",
    "summary": "Dynamic Configure-Price-Quote-style generation of products",
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["product"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_attribute.xml",
        "views/product_product.xml",
        "views/product_template.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cpq/static/src/components/**/*.js",
            "cpq/static/src/components/**/*.xml",
        ],
    },
    "license": "LGPL-3",
}
