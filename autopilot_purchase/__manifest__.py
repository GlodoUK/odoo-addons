{
    "name": "autopilot_purchase",
    "summary": "Generic purchase-EDI engine (export purchase orders) for autopilot "
    "connectors",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Purchases",
    "version": "19.0.1.1.0",
    "depends": [
        "purchase",
        "queue_job",
        "autopilot",
    ],
    "external_dependencies": {"python": ["fsspec"]},
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/autopilot_purchase_backend_views.xml",
        "views/autopilot_purchase_binding_views.xml",
        "views/purchase_order_views.xml",
    ],
    "license": "Other proprietary",
}
