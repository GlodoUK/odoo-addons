{
    "name": "autopilot",
    "summary": "Declarative cron/automation helpers and ETL tools for building "
    "lightweight connectors",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Technical",
    "version": "19.0.1.2.0",
    "icon": "/autopilot/static/description/icon.svg",
    "depends": [
        "base",
        "base_automation",
        "queue_job",
    ],
    "external_dependencies": {
        "python": ["fsspec", "openpyxl", "paramiko", "xlrd", "xlwt"]
    },
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/menus.xml",
        "views/autopilot_connection_views.xml",
        "views/autopilot_activity_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "autopilot/static/src/navbar/navbar.scss",
        ],
    },
    "license": "LGPL-3",
}
