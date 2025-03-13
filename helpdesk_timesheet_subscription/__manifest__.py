# Copyright © 2021 Glo Systems (<https://www.glo.systems>)
# @author: Vasiliy Nickolayev (UA) (<info@glo.systems>)
# License Other proprietary
# (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Timesheet Subscription",
    "version": "15.0.0.0.1",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Adds ability for users to buy support/development time,"
    " shows users available time balance",
    "depends": [
        "base",
        "mail",
        "portal",
        "project",
        "contacts",
        "hr_timesheet",
        "sale_management",
        "sale_timesheet",
        "sale_subscription",
        "helpdesk",
        "helpdesk_timesheet",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/product_template.xml",
        "data/sale_subscription_template.xml",
        "views/glo_partner_time_balance.xml",
        "views/glo_partner_time_balance_history.xml",
        "views/helpdesk_portal_template.xml",
        "views/helpdesk_team.xml",
        "views/helpdesk_ticket.xml",
        "views/hr_employee.xml",
        "views/product_template.xml",
        "views/project_task.xml",
        "views/res_partner.xml",
        "wizards/glo_post_msg_log_time_wizard.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "helpdesk_timesheet_subscription/static/src/js/portal_chatter.js",
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
