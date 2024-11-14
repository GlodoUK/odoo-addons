{
    "name": "connector_edi_protocol_ftp",
    "summary": "EDI FTP Protocol Support",
    "version": "17.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["connector_edi"],
    "data": ["views/edi_route.xml"],
    "external_dependencies": {
        "deb": ["libcurl4-openssl-dev"],
        "python": ["ftpparser", "pycurl"],
    },
    "license": "Other proprietary",
}
