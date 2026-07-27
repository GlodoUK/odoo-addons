{
    "name": "rss",
    "summary": "RSS and Atom feed reader.",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Productivity",
    "version": "19.0.2.0.0",
    "depends": ["mail"],
    "external_dependencies": {"python": ["feedparser", "requests"]},
    "data": [
        "security/ir.model.access.csv",
        "security/rss_security.xml",
        "data/cron.xml",
        "views/rss_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "rss/static/src/scss/rss_kanban.scss",
        ],
    },
    "license": "LGPL-3",
}
