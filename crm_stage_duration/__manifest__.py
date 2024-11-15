{
    "name": "CRM Stage Duration",
    "summary": """
        Monitors and adds stage duration on kanban and tree views, and also the chatter""",  # noqa: E501
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "16.0.0.0.0",
    "depends": ["base", "crm"],
    "data": [
        "security/ir.model.access.csv",
        "views/crm_lead.xml",
    ],
    "external_dependencies": {"python": ["human_readable"]},
    "license": "AGPL-3",
    "demo": [],
}
