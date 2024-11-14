{
    "name": "cpq_mrp",
    "summary": "Glue module between CPQ and MRP",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/cpq",
    "category": "Manufacturing/Manufacturing",
    "version": "17.0.1.1.0",
    "depends": ["cpq", "mrp"],
    "auto_install": True,
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/dynamic_bom.xml",
        "views/dynamic_bom_line.xml",
        "views/stock_picking.xml",
        "views/stock_move_line.xml",
        "views/product.xml",
        "views/menu.xml",
    ],
    "license": "LGPL-3",
}
