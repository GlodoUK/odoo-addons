{
    "name": "Concurrency Warning",
    "summary": "Issue a visual warning and reload the page content if a user"
    " has left a model open, and it has been altered in the meantime.",
    "version": "18.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": [
        "bus",
        "base",
        "base_automation",
    ],
    "data": [
        "views/ir_actions_server.xml",
    ],
    "assets": {
        "web.assets_backend": ["concurrency_warning/static/src/js/poke.esm.js"],
    },
    "license": "LGPL-3",
}
