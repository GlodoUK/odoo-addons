{
    "name": "CRM Stage Duration",
    "summary": """
        Monitors and adds stage duration on kanban and tree views, and also the chatter""",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/GlodoUK/crm",
    "category": "Uncategorized",
    "version": "16.0.0.0.0",
    "depends": ["base", "crm"],
    "data": [
        "security/ir.model.access.csv",
        "views/crm_lead.xml",
    ],
    "external_dependencies": {"python": ["human_readable"]},
    "license": "Other proprietary",
    "demo": [],
}
