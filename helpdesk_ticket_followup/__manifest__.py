# Copyright © 2021 Glo Systems (<https://www.glo.systems>)
# @author: Vasiliy Nickolayev (UA) (<info@glo.systems>)
# License Other proprietary
# (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Ticket Followup",
    "version": "15.0.0.0.1",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Automates ticket followups for customer update stage"
    " with ability to snooze them",
    "depends": [
        "base",
        "portal",
        "helpdesk",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "data/helpdesk_stage.xml",
        "data/followup_mail_template.xml",
        "views/helpdesk_stage.xml",
        "views/helpdesk_ticket_followup.xml",
        "views/portal_my_ticket_followup.xml",
        "views/res_config_settings.xml",
        "views/res_partner.xml",
    ],
    "assets": {},
    "demo": [],
    "external_dependencies": {},
    "post_init_hook": "_setup_default_settings",
    "price": 0.0,
    "currency": "EUR",
    "support": "info@glo.systems",
    "application": False,
    "installable": True,
    "auto_install": False,
}
