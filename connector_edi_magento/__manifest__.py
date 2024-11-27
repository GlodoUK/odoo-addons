{
    "name": "connector_edi_magento",
    "summary": """
        EDI integrations for Magento""",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Technical",
    "version": "16.0.1.0.0",
    "depends": [
        "connector_edi",
        "connector_edi_sale",
        "connector_edi_product",
        "connector_edi_res_partner",
    ],
    "data": [
        "views/edi_backend.xml",
        "views/magento.xml",
        "views/product.xml",
        "views/edi_envelope_route.xml",
        "data/account.xml",
        "wizards/update_attribute.xml",
        "security/ir.model.access.csv",
        "views/res_partner.xml",
    ],
    "demo": [],
    "license": "Other proprietary",
    "external_dependencies": {
        "python": [
            "requests_oauthlib",
            "oauthlib",
        ]
    },
}
