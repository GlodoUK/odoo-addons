{
    "name": "mail_autofollow",
    "summary": "Automatically subscribe followers to records matching a rule",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Productivity/Discuss",
    "version": "19.0.1.0.0",
    "depends": ["mail"],
    "data": [
        "security/mail_autofollow_security.xml",
        "security/ir.model.access.csv",
        "views/mail_autofollow_rule_views.xml",
        "views/menus.xml",
    ],
    "license": "LGPL-3",
}
