{
    "name": "delivery_parcelhub_whistl",
    "summary": """Connector to integrate with Parcelhub/Whistl courier""",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    "version": "18.0.1.0.0",
    "depends": [
        "delivery_carrier_validation",
        "delivery_state_events",
        "sale_stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/delivery_carrier.xml",
        "views/stock_picking.xml",
    ],
    "demo": [],
    "license": "LGPL-3",
}
