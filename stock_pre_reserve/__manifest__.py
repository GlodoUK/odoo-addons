{
    "name": "stock_pre_reserve",
    "summary": """Link an existing outbound move to a new inbound move
 manually, allowing reservations against inbound stock.
    """,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/stock-delivery",
    "category": "Uncategorized",
    "version": "17.0.1.1.0",
    "depends": ["stock", "sales_team", "stock_picking_move_form"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/stock_move_reserve.xml",
        "views/stock_picking.xml",
    ],
    "license": "AGPL-3",
}