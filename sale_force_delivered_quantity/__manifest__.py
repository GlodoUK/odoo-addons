{
    "name": "sale_force_delivered_quantity",
    "summary": "Count a quantity as delivered on a sale order line without moving it",
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    # sale_mrp for the kit branch of _get_qty_procurement, which answers from
    # the kit's moves without calling super: this module has to sit above it
    "depends": ["sale_stock", "sale_mrp"],
    "data": [
        "views/sale_order.xml",
    ],
    "license": "Other proprietary",
}
