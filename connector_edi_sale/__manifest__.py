{
    "version": "15.0.1.0.0",
    "name": "connector_edi_sale",
    "summary": """
    EDI Sales module
    """,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": [
        "connector_edi",
        "sale_stock",
        "delivery",
        "stock_picking_component_events",
        "account_invoice_component_events",
    ],
    "data": [
        "data/edi_route_event.xml",
        "security/ir.model.access.csv",
        "views/sale_order.xml",
        "views/edi_sale_order.xml",
        "views/edi_backend.xml",
        "views/edi_message.xml",
    ],
    "license": "LGPL-3",
    "external_dependencies": {"bin": [], "python": []},
}
