{
    "name": "stock_picking_merge",
    "summary": "Adds the ability to merge stock.picking records",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "19.0.1.0.0",
    "depends": ["stock"],
    "license": "LGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "data/server_action.xml",
        "views/stock_picking_type.xml",
        "views/stock_picking_merge_message_templates.xml",
        "wizards/stock_picking_merge_wizard.xml",
    ],
}
