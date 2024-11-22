{
    "version": "12.0.1.0.0",
    "name": "queue_job_duration",
    "summary": "Adds a time elapsed field to the job queue",
    "category": "Hidden",
    "images": [],
    "application": False,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "depends": ["queue_job"],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        'views/views.xml',
    ],
    "qweb": [],
    "demo": [],
    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "uninstall_hook": None,
    "auto_install": False,
    "installable": True,
}
