{
    "name": "mail_res_partner_forward",
    "summary": "Rule based forwarding of email to other partners",
    "version": "15.0.1.0.0",
    "category": "Productivity/Discuss",
    "author": "Glo Networks",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["mail"],
    "external_dependencies": {"python": ["odoo_test_helper"], "bin": []},
    "data": [
        "security/ir.model.access.csv",
        "views/res_user.xml",
        "views/res_partner.xml",
        "views/res_partner_forwarding_rule.xml",
    ],
    "website": "https://github.com/GlodoUK/odoo-addons",
}
