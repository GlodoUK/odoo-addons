{
    "name": "stock_picking_state_duration",
    "summary": "Show how long a transfer has been in its current state",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Inventory",
    "version": "19.0.1.0.0",
    "depends": [
        "stock",
    ],
    "data": [
        "views/stock_picking_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "stock_picking_state_duration/static/src/state_duration_field.esm.js",
            "stock_picking_state_duration/static/src/state_duration_field.xml",
        ],
    },
    "pre_init_hook": "pre_init_hook",
    "license": "Other proprietary",
}
