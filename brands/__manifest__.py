{
    "version": "15.0.2.0.0",
    "name": "brands",
    "summary": "Allows a sale order and product to be associated with a brand",
    "category": "Sales",
    "application": True,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "depends": ["sale", "product"],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        "security/ir.model.access.csv",
        "report/sale_report.xml",
        "report/account_invoice_report_view.xml",
        "views/views.xml",
        "data/data.xml",
    ],
}
