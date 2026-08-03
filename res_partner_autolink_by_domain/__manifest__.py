{
    "name": "Partner Autolink by Email Domain",
    "summary": "File contacts emailing in under the contact owning their domain",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "19.0.1.0.0",
    "depends": ["contacts"],
    "external_dependencies": {"python": ["idna"]},
    "data": [
        "security/ir.model.access.csv",
        "data/res.partner.email.domain.ban.csv",
        "views/res_partner_email_domain_ban.xml",
        "views/res_partner.xml",
    ],
    "license": "LGPL-3",
}
