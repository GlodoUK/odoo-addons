{
    "name": "autopilot",
    "summary": "Declarative cron/automation helpers and ETL tools for building "
    "lightweight connectors",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Technical",
    "version": "19.0.1.0.0",
    "icon": "/autopilot/static/description/icon.svg",
    "depends": [
        "base",
        "base_automation",
        "queue_job",
    ],
    "external_dependencies": {"python": ["openpyxl", "xlrd", "xlwt"]},
    "data": [
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "autopilot/static/src/overview/**/*",
        ],
    },
    "license": "LGPL-3",
}
