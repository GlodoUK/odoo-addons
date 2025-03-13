# Copyright © 2021 Glo Systems (<https://www.glo.systems>)
# @author: Vasiliy Nickolayev (UA) (<info@glo.systems>)
# License Other proprietary
# (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Teams Message",
    "version": "15.0.0.0.1",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Sends messages to teams chat",
    "depends": [
        "base",
        "base_setup",
        "helpdesk",
        "helpdesk_ticket_followup",
    ],
    "data": [
        "views/res_config_settings.xml",
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
