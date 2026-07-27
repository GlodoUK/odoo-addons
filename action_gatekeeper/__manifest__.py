{
    "name": "action_gatekeeper",
    "summary": """
    Provides a Gatekeeper Mixin to prevent actions or to trigger specific reactions
    based on defined rules.
    """,
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Technical",
    "depends": [],
    "data": [
        "security/ir.model.access.csv",
        "views/gatekeeper_rule_views.xml",
        "views/gatekeeper_line_views.xml",
        "data/data.xml",
    ],
    "license": "Other proprietary",
}
