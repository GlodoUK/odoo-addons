{
    "name": "Gate",
    "summary": "Hard, rule-driven approval gates on record actions (edit-safe, waterfall tiers)",
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["base"],
    "data": [
        "security/gate_security.xml",
        "security/ir.model.access.csv",
        "views/gate_rule_views.xml",
        "views/gate_hold_views.xml",
        "views/gate_menus.xml",
    ],
    "license": "LGPL-3",
}
