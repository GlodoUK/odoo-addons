# Copyright © 2021 Glo Systems (<https://www.glo.systems>)
# @author: Karl Southern (<info@glo.systems>)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Create Multiple Portal Users",
    "version": "15.0.1.0.1",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Lets create multiple portal users from company's contact page",
    "depends": [
        "base",
        "portal",
        "helpdesk",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner.xml",
        "wizards/add_users_to_company_wizard.xml",
    ],
    "assets": {},
    "demo": [],
    "external_dependencies": {},
    "price": 0.0,
    "currency": "EUR",
    "support": "info@glo.systems",
    "application": False,
    "installable": True,
    "auto_install": False,
}
