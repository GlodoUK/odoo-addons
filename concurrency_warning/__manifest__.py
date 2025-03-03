{
    "name": "concurrency_warning",
    "summary": """Issue a concurrency warning if a user has left a model
    open, and it been altered in the meantime.""",
    "description": """Issue a concurrency warning if a user has left a model
    open, and it been altered in the meantime.""",
    "author": "Glodo",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "12.0.1.0.0",
    "depends": [
        "base",
        "base_automation",
        "sale_management",
        "purchase"
    ],
    "data": ["data/base_automation.xml", "views/templates.xml"],
    "demo": [],
    "license": "LGPL-3",
}
