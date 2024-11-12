{
    "name": "sale_order_hold_stock_picking_hold",
    "summary": """
    Integrates sale_order_hold with stock_picking_hold
    """,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/stock-delivery",
    "category": "Uncategorized",
    "version": "15.0.1.0.0",
    "depends": [
        "sale_stock",
        "stock_picking_hold",
        "sale_order_hold",
    ],
    "data": ["views/stock_picking.xml"],
    "demo": [],
    "auto_install": True,
    "license": "LGPL-3",
}
