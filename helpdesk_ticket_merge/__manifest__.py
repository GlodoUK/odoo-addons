{
    "name": "helpdesk_ticket_merge",
    "summary": """
        Merge helpdesk tickets including all ticktet history and attachments.
    """,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Helpdesk",
    "version": "18.0.1.0.0",
    "depends": ["helpdesk"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/merge_wizard.xml",
    ],
    "demo": [],
    "license": "Other proprietary",
}
