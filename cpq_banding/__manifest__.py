{
    "name": "cpq_banding",
    "summary": "Banding/Fabric Custom Values",
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["cpq", "sale_stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/cpq_banding_views.xml",
        "views/product_attribute_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cpq_banding/static/src/components/*.xml",
        ],
    },
    "license": "LGPL-3",
}
