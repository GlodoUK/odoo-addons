# Copyright © 2021 Glo Systems (<https://www.glo.systems>)
# @author: Karl Southern (<info@glo.systems>)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Sale Order Link",
    "version": "15.0.1.0.2",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Links Sales Orders to Helpdesk Tickets",
    "depends": [
        "base",
        "helpdesk",
        "sale",
    ],
    "data": [
        "views/helpdesk_ticket.xml",
        "views/sale_order.xml",
        "views/helpdesk_ticket_portal.xml",
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
