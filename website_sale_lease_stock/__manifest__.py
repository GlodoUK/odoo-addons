{
    "name": "website_sale_lease_stock",
    "summary": "Leasing: Integrates sale_stock_lease with website_sale",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Website",
    "version": "14.0.1.0.1",
    "depends": ["website_sale", "sale_lease_stock"],
    "data": [
        "security/ir.model.access.csv",
        "security/website_sale_lease_stock.xml",
        "views/website_sale.xml",
        "views/assets.xml",
    ],
    "license": "Other proprietary",
}
