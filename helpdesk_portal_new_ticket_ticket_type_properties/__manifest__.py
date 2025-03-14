{
    "name": "Website Helpdesk Ticket Create Ticket Type Properties",
    "summary": "Glue module between website_helpdesk_ticket_create and helpdesk_ticket_type_properties.",  # noqa
    "version": "16.0.1.0.0",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["helpdesk_ticket_type_properties", "helpdesk_portal_new_ticket"],
    "auto_install": True,
    "data": ["views/helpdesk_portal_templates.xml"],
    "assets": {
        "web.assets_frontend": [
            "helpdesk_portal_new_ticket_ticket_type_properties/static/src/js/portal_ticket_type_edit.esm.js",  # noqa
        ]
    },
    "license": "Other proprietary",
}
