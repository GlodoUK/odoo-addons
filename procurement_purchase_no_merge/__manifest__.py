{
    "version": "12.0.1.0.1",
    "name": "procurement_purchase_no_merge",
    "summary": "Prevent POs merging, create 1:1 relationship for SO:PO",
    "category": "Purchases",
    "application": False,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["sale_purchase", "sale_stock"],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        "views/views.xml",
    ],
    'license': 'AGPL-3',
}
