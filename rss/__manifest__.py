{
    "name": "rss",
    "summary": "RSS and Atom feed reader.",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Productivity",
    "version": "20.0.1.0.0",
    "depends": ["mail"],
    "external_dependencies": {"python": ["feedparser", "requests"]},
    "data": [
        "security/ir.access.csv",
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
