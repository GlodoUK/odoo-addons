# Copyright © 2022 Glo Systems (<https://www.glo.systems>)
# @author: Vasiliy Nickolayev (UA) (<info@glo.systems>)
# License Other proprietary
# (https://www.odoo.com/documentation/15.0/legal/licenses.html).

{
    "name": "Helpdesk Timesheet Report",
    "version": "15.0.0.0.1",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Creates reports on tickets and logged time",
    "depends": [
        "base",
        "portal",
        "project",
        "hr_timesheet",
        "helpdesk",
        "helpdesk_timesheet",
        "helpdesk_timesheet_subscription",
    ],
    "data": [
        "views/account_analytic_line.xml",
        "views/hr_timesheet_report_menu.xml",
        "views/hr_timesheet_report_by_company.xml",
        "views/hr_timesheet_report_by_company_ticket_engineer.xml",
        "views/hr_timesheet_report_by_engineer.xml",
        "views/hr_timesheet_report_by_ticket_type_category.xml",
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
