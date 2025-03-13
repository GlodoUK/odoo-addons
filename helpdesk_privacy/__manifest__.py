{
    "name": "Helpdesk Privacy",
    "version": "16.0.1.0.0",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Adds private tickets with limited access",
    "depends": [
        "helpdesk",
        "helpdesk_portal_new_ticket",
    ],
    "data": [
        "views/helpdesk_portal_templates.xml",
        "views/helpdesk_ticket.xml",
        "views/templates.xml",
        "security/helpdesk_ticket.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "helpdesk_privacy/static/src/js/ticket_actions.js",
        ],
    },
}
