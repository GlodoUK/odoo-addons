{
    "name": "cpq",
    "summary": "Dynamic Configure-Price-Quote-style generation of products",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/cpq",
    "category": "Sales/Sales",
    "version": "15.0.1.1.0",
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
    "license": "Other proprietary",
    "assets": {
        "web.assets_backend": [
            "cpq/static/src/components/**/*.js",
        ],
        "web.assets_qweb": [
            "cpq/static/src/components/**/*.xml",
        ],
    },
}
