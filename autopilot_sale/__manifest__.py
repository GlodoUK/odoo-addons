{
    "name": "autopilot_sale",
    "summary": "Generic sale-EDI engine (import order / acknowledge / dispatch / "
    "invoice) for autopilot connectors",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    "version": "19.0.1.1.0",
    "depends": [
        "sale_stock",
        "account",
        "stock",
        "queue_job",
        "utm",
        "autopilot",
    ],
    "external_dependencies": {"python": ["fsspec"]},
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/autopilot_sale_data.xml",
        "views/autopilot_sale_backend_views.xml",
        "views/autopilot_sale_connection_views.xml",
        "views/autopilot_sale_binding_views.xml",
        "wizards/autopilot_sale_upload_wizard_views.xml",
    ],
    "license": "LGPL-3",
}
