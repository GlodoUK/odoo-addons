{
    "name": "Helpdesk Privacy",
    "version": "18.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["helpdesk_commercial_partner"],
    "data": [
        "security/helpdesk_ticket.xml",
        "views/helpdesk_portal_templates.xml",
        "views/helpdesk_ticket_views.xml",
    ],
    "web.assets_frontend": [
        "helpdesk_privacy/static/src/js/*.js",
    ],
    "license": "Other proprietary",
}
