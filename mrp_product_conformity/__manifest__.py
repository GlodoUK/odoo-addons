{
    "name": "MRP Product Conformity",
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["mrp"],
    "data": [
        "security/ir.model.access.csv",
        "security/product_conformity_security.xml",
        "data/ir_actions_server_data.xml",
        "data/ir_cron_data.xml",
        "data/ir_sequence_data.xml",
        "views/mrp_production_views.xml",
        "views/product_conformity_alert_views.xml",
        "views/product_product_views.xml",
        "views/product_template_views.xml",
    ],
    "license": "Other proprietary",
}
