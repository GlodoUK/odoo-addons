{
    "name": "action_gatekeeper_sale_stock_hold",
    "summary": """
    Gatekeeper can place stock pickings on hold.
    """,
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Inventory",
    "depends": ["action_gatekeeper_sale", "stock_picking_hold"],
    "data": [
        "views/stock_picking_views.xml",
    ],
    "license": "Other proprietary",
    "auto_install": True,
}
