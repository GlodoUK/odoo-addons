{
    "version": "15.0.1.0.0",
    "name": "connector_edi_protocol_ssh",
    "summary": """
    EDI SFTP and SCP Protocol Support
    """,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["connector_edi"],
    "data": ["views/edi_route.xml"],
    "license": "LGPL-3",
    "external_dependencies": {
        "bin": [],
        # cryptography<37 is to maintain compat with odoo15.0
        "python": ["paramiko", "scp", "cryptography<37"],
    },
}
