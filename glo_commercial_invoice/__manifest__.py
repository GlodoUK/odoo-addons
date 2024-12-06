{
    "name": "glo_commercial_invoice",
    "summary": "Glo Commercial Invoice",
    "version": "17.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "author": "Glo Networks",
    "license": "LGPL-3",
    "depends": ["sale", "stock", "sale_stock", "account_intrastat"],
    "data": [
        "views/stock_picking_views.xml",
        "report/glo_commercial_invoice_views.xml",
        "report/stock_report_views.xml",
    ],
}
