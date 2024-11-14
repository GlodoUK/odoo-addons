{
    "name": "cpq_banding",
    "summary": "Banding/Fabric Custom Values",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "depends": [
        "sale_stock",
        "cpq",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_attribute.xml",
        "views/product_banding.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cpq_banding/static/src/components/*.xml",
        ],
    },
}
