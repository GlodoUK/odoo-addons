# Copyright © 2022 Glo Systems (<https://www.glo.systems>)
# @author: Karl Southern (<info@glo.systems>)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Team Ticket Sequence",
    "version": "15.0.1.0.1",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Sets up automatically custom number assignment for helpdesk tickets",
    "depends": [
        "base",
        "portal",
        "helpdesk",
    ],
    "data": [
        "views/helpdesk_portal_templates.xml",
        "views/helpdesk_team.xml",
        "views/helpdesk_ticket.xml",
        "views/ir_sequence.xml",
    ],
    "assets": {},
    "demo": [],
    "external_dependencies": {},
    "post_init_hook": "_post_init_setup_sequence",
    "price": 0.0,
    "currency": "EUR",
    "support": "info@glo.systems",
    "application": False,
    "installable": True,
    "auto_install": False,
}
