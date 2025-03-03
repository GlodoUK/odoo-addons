{
    "name": "delivery_state_events",
    "summary": "Provides fields and methods to support tracking a shipment",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Delivery",
    "version": "14.0.1.0.1",
    "depends": ["delivery", "queue_job"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_picking.xml",
        "views/delivery_carrier.xml",
        "data/cron.xml",
    ],
    "demo": [],
    "license": "AGPL-3",
}
