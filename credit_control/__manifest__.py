{
    "name": "credit_control",
    "summary": """
    Credit Control Policies
    """,
    "author": "Glo Networks",
    "license": "Other proprietary",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Invoicing &amp; Payments",
    "version": "17.0.0.0.0",
    "depends": ["account", "sale", "mail", "website_sale"],
    "data": [
        "data/mail_activity.xml",
        "security/ir.model.access.csv",
        "views/credit_control_policy.xml",
        "views/res_partner.xml",
        "views/sale.xml",
    ],
    "demo": [],
}
