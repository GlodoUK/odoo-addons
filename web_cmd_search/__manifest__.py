{
    "name": "web_cmd_palette_search",
    "summary": "Adds a global command search to quick access records",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "16.0.1.0.0",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/provider.xml",
    ],
    "assets": {
        "web.assets_backend": ["web_cmd_search/static/src/**/*"],
    },
    "license": "LGPL-3",
}
