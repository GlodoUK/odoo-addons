{
    "name": "Connector EDI Sale",
    "version": "18.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": [
        "base_sparse_field",
        "connector_edi",
        "account_invoice_component_events",
        "stock_picking_component_events",
        "delivery",
        "sale_stock",
    ],
    "data": [
        "data/edi_route_event_data.xml",
        "security/ir.model.access.csv",
        "views/edi_backend_views.xml",
        "views/edi_message_views.xml",
        "views/edi_sale_order_views.xml",
        "views/sale_order_views.xml",
    ],
    "license": "Other proprietary",
}
