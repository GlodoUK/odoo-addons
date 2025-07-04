{
    "name": "delivery_carrier_validation",
    "summary": "Utility module to add a validation step before send_to_shipper",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "18.0.1.0.0",
    "depends": ["stock_delivery"],
    "license": "LGPL-3",
    "external_dependencies": {"python": ["odoo-test-helper"]},
    "data": [
        "views/delivery_carrier.xml",
    ],
}
