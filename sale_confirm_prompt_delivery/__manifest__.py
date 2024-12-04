{
    "name": "sale_confirm_prompt_delivery",
    "summary": "Prompt users to add delivery to a sale, if it's missing",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Sales",
    "version": "15.0.1.0.0",
    "depends": ["sale_management"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order.xml",
        "wizards/sale_order_missing_delivery.xml",
    ],
    "demo": [],
    "license": "LGPL-3",
}
