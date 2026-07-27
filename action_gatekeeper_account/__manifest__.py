{
    "name": "action_gatekeeper_account",
    "summary": """
    Addon to Action Gatekeeper for Accounts/Invoice Support.
    """,
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Technical",
    "depends": ["action_gatekeeper", "account"],
    "data": [
        "views/account_move_views.xml",
        "views/gatekeeper_rule_views.xml",
        "data/data.xml",
    ],
    "license": "Other proprietary",
}
