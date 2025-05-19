{
    "name": "delivery_spring",
    "summary": "Connector to integrate with Spring courier",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    "version": "18.0.1.0.0",
    "depends": [
        "delivery_state_events",
        "sale_stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/delivery_carrier.xml",
    ],
    "demo": [],
    "license": "LGPL-3",
}
