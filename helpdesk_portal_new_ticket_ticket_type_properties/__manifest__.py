{
    "name": "Website Helpdesk Ticket Create Ticket Type Properties",
    "version": "19.0.1.0.0",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["helpdesk_portal_new_ticket", "helpdesk_ticket_type_properties"],
    "data": ["views/helpdesk_portal_templates.xml"],
    "assets": {
        "web.assets_frontend": [
            "helpdesk_portal_new_ticket_ticket_type_properties/static/src/js/*.esm.js",
        ]
    },
    "auto_install": True,
    "license": "Other proprietary",
}
