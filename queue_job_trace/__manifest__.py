{
    "name": "Job Queue Trace",
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "LGPL-3",
    "category": "Generic Modules",
    "summary": "Correlate jobs spawned from the same origin with a trace id",
    "depends": ["queue_job"],
    "data": [
        "views/queue_job_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
}
