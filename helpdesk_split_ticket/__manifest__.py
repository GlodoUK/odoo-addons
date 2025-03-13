# Copyright © 2021 Glo Systems (<https://www.glo.systems>)
# @author: Karl Southern (<info@glo.systems>)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Split Ticket",
    "version": "15.0.1.0.1",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Split/Create new tickets from chatter messages",
    "depends": [
        "base",
        "mail",
        "helpdesk",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/split_ticket_wizard.xml",
    ],
    "qweb": [
        "static/src/components/message/message.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/helpdesk_split_ticket/static/src/components/message/message.esm.js",
        ]
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
