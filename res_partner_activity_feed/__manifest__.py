{
    "name": "Partner Activity Feed",
    "summary": "HubSpot-style activity feed on the partner form, built on mail.message",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "19.0.1.0.0",
    "development_status": "Alpha",
    "depends": ["mail"],
    "data": [
        "views/mail_message_views.xml",
        "views/res_partner_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "res_partner_activity_feed/static/src/**/*",
        ],
    },
    "license": "Other proprietary",
}
