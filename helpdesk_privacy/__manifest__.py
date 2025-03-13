# Copyright © 2021 Glo Systems (<https://www.glo.systems>)
# @author: Karl Southern (<info@glo.systems>)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Privacy",
    "version": "15.0.1.0.1",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Adds private tickets with limited access",
    "depends": [
        "base",
        "helpdesk",
        "helpdesk_portal_new_ticket",
    ],
    "data": [
        "views/helpdesk_portal_templates.xml",
        "views/helpdesk_ticket.xml",
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "helpdesk_privacy/static/lib/css/select2.min.css",
            "helpdesk_privacy/static/lib/js/select2.min.js",
            "helpdesk_privacy/static/src/js/apply_select2.js",
            "helpdesk_privacy/static/src/js/tickets_actions.js",
        ],
    },
    "demo": [],
    "external_dependencies": {},
    "price": 0.0,
    "currency": "EUR",
    "support": "info@glo.systems",
    "application": False,
    "installable": True,
    "auto_install": False,
}
