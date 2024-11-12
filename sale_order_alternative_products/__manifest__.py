{
    "name": "Sale Order Alternative Products",
    "summary": """
        Module to propose alternative products at the
         time of Sale Order Line  product selection.
    """,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/stock-delivery",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/
    # odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Base",
    "version": "15.0.2.0.0",
    # any module necessary for this one to work correctly
    "depends": [
        "stock",
        "sale",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order.xml",
        "wizards/wizard_suggest_alternatives.xml",
        "views/product.xml",
        "views/res_config.xml",
    ],
    "license": "AGPL-3",
}
