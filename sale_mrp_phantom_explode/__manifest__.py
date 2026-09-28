{
    "name": "sale_mrp_phantom_explode",
    "summary": "Allow a phantom kit to explode on a sale order",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "19.0.1.0.0",
    "depends": ["sale", "mrp"],
    "data": [
        "views/mrp_bom.xml",
        "views/sale_order.xml",
    ],
    "license": "Other proprietary",
    "assets": {
        "web.assets_backend": [
            "sale_mrp_phantom_explode/static/src/**/*",
        ],
    },
}
