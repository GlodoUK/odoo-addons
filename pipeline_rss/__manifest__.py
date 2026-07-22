{
    "name": "pipeline_rss",
    "summary": "RSS reader using observable delayed method pipelines.",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Pipeline",
    "version": "19.0.1.4.0",
    "depends": ["mail", "pipeline"],
    "external_dependencies": {"python": ["feedparser", "requests"]},
    "data": [
        "security/ir.model.access.csv",
        "security/rss_security.xml",
        "data/cron.xml",
        "views/rss_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pipeline_rss/static/src/scss/rss_kanban.scss",
        ],
    },
    "license": "LGPL-3",
}
