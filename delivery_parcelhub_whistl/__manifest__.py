{
    "name": "delivery_parcelhub_whistl",
    "summary": """Connector to integrate with Parcelhub/Whistl courier""",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    "version": "15.0.1.0.0",
    "depends": [
        "delivery",
        "delivery_state_events",
        "sale_stock",
    ],
    "data": [
        "views/views.xml",
        "data/data.xml",
        # "security/ir.model.access.csv",
    ],
    "demo": [],
    "license": "AGPL-3",
}
