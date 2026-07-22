{
    "name": "credit_control",
    "summary": """
    Credit Control Policies
    """,
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Invoicing &amp; Payments",
    "depends": ["account", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_activity_data.xml",
        "views/credit_control_policy_views.xml",
        "views/credit_control_rule_views.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
    ],
    "license": "Other proprietary",
}
