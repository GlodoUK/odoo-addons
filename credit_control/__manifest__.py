{
    "name": "credit_control",
    "summary": """
    Credit Control Policies
    """,
    "author": "Glo Networks",
    "license": "Other proprietary",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Invoicing &amp; Payments",
    "version": "16.0.1.0.0",
    "depends": ["account", "sale", "mail"],
    "data": [
        "data/groups.xml",
        "data/mail_activity.xml",
        "security/ir.model.access.csv",
        "views/credit_control_policy.xml",
        "views/res_partner.xml",
        "views/sale.xml",
    ],
}
