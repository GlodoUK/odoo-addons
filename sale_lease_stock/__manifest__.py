{
    "name": "sale_lease_stock",
    "summary": "Leasing using Stock (rental-lite)",
    "author": "Glodo",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    "version": "14.0.1.0.0",
    "depends": ["sale_stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/product.xml",
        "views/sale.xml",
        "views/lease_schedule.xml",
        "views/res_partner.xml",
        "data/cron.xml",
    ],
    "demo": [],
    "license": "Other proprietary",
}
