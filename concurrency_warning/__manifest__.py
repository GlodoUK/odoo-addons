{
    "name": "concurrency_warning",
    "summary": """Issue a visual warning and reload
    the page content if a user has left a model
    open, and it been altered in the meantime.""",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "15.0.1.0.0",
    "depends": [
        "bus",
        "base_automation",
    ],
    "data": [],
    "demo": [],
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": ["/concurrency_warning/static/src/js/client_poke.esm.js"],
    },
}
