{
    "name": "res_partner_multi_phone",
    "summary": "Adds multiple phone numbers to Contacts",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Customizations",
    "version": "14.0.1.0.0",
    "depends": ["contacts", "phone_validation"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner.xml",
    ],
    "demo": [],
    "license": "LGPL-3",
}
