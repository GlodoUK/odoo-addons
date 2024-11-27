{
    "version": "14.0.1.0.0",
    "name": "connector_edi",
    "summary": """
    Base EDI module
    """,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": [
        "base_setup",
        "base_sparse_field",
        "connector",
        "component",
        "queue_job",
    ],
    "data": [
        "views/edi_message.xml",
        "views/edi_envelope.xml",
        "views/edi_backend.xml",
        "views/edi_message_route.xml",
        "views/edi_route_event.xml",
        "views/edi_envelope_route.xml",
        "views/menu.xml",
        "security/ir.model.access.csv",
        "data/edi_route_event.xml",
        "data/edi_sequences.xml",
        "data/mail.xml",
    ],
    "license": "Other proprietary",
    "external_dependencies": {"bin": [], "python": ["requests", "lxml"]},
}
