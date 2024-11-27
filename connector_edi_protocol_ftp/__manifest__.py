{
    "version": "14.0.1.0.0",
    "name": "connector_edi_protocol_ftp",
    "summary": """
    EDI FTP Protocol Support
    """,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["connector_edi"],
    "data": ["views/edi_route.xml"],
    "license": "Other proprietary",
    "external_dependencies": {
        "bin": [],
        "python": ["pycurl", "ftpparser"],
        "deb": ["libcurl4-openssl-dev", "libssl-dev"],
    },
}
