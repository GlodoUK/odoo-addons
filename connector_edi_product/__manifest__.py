{
    "version": "15.0.1.0.0",
    "name": "connector_edi_product",
    "summary": """
    EDI Product module
    """,
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/edi",
    "depends": [
        "connector_edi",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product.xml",
        "views/edi_product.xml",
        "views/edi_message.xml",
        "data/events.xml",
    ],
    "license": "Other proprietary",
    "external_dependencies": {"bin": [], "python": []},
}
