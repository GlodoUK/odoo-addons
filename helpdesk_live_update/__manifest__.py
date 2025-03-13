# Copyright © 2021 Glo Systems (<https://www.glo.systems>)
# @author: Matt Lipski (<info@glo.systems>)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Live Update",
    "version": "15.0.1.0.1",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Updates helpdesk tickets automatically while open",
    "depends": [
        "base",
        "base_automation",
        "helpdesk",
        "concurrency_warning",
    ],
    "data": [
        "data/base_automation.xml",
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
