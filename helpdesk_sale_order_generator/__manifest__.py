# Copyright © 2022 Glo Systems (<https://www.glo.systems>)
# @author: Vasiliy Nickolayev (UA) (<info@glo.systems>)
# License Other proprietary
# (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Sale Order Generator",
    "version": "18.0.1.0.1",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Generates Quotation from helpdesk",
    "depends": [
        "base",
        "helpdesk",
        "sale",
        "helpdesk_sale_order_link",
    ],
    "data": [
        "views/helpdesk_ticket.xml",
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
