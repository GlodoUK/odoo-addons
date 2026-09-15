{
    "name": "sale_delivery_auto",
    "summary": "Assign the first available delivery carrier and keep the "
    "shipping cost up to date, without trampling manual edits",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Inventory/Delivery",
    "version": "19.0.1.0.0",
    "depends": ["sale", "delivery"],
    # Each of these answers the same question its own way, and two answers is
    # worse than either: the OCA pair assigns and re-rates on their own terms,
    # and sale_delivery_required blocks a confirmation this module deliberately
    # allows - an order whose shipping cost line was deleted.
    "excludes": [
        "delivery_auto_refresh",
        "sale_delivery_required",
        "sale_order_carrier_auto_assign",
    ],
    "data": [
        "views/sale_order.xml",
    ],
    "license": "LGPL-3",
}
